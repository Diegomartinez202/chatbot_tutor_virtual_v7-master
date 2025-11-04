import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { Bot, RefreshCw } from "lucide-react";
import ChatUI from "@/components/chat/ChatUI";
import ChatbotLoading from "@/components/ChatbotLoading";
import ChatbotStatusMini from "@/components/ChatbotStatusMini";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";
import { connectChatHealth } from "@/services/chat/health";
import { connectWS } from "@/services/chat/connectWS";
import Harness from "@/pages/Harness";
import { STORAGE_KEYS } from "@/lib/constants";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";
const CHAT_REST_URL =
    import.meta.env.VITE_CHAT_REST_URL || `${API_BASE.replace(/\/$/, "")}/chat`;
const RASA_HTTP_URL =
    import.meta.env.VITE_RASA_REST_URL || import.meta.env.VITE_RASA_HTTP || "/rasa";
const RASA_WS_URL =
    import.meta.env.VITE_RASA_WS_URL || import.meta.env.VITE_RASA_WS || "/ws";

const DEFAULT_BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const SHOW_HARNESS = import.meta.env.VITE_SHOW_CHAT_HARNESS === "true";
const CHAT_REQUIRE_AUTH = import.meta.env.VITE_CHAT_REQUIRE_AUTH === "true";
const TRANSPORT = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();
const USER_SETTINGS_URL =
    (import.meta.env.VITE_USER_SETTINGS_URL &&
        String(import.meta.env.VITE_USER_SETTINGS_URL).trim()) ||
    "/api/me/settings";

const AUTO_MINIMIZE = import.meta.env.VITE_AUTO_MINIMIZE_WIDGET === "true";

function applyPrefsToDocument(prefs, i18n) {
    try {
        const html = document.documentElement;
        const dark = prefs?.theme === "dark";
        const hc = !!prefs?.highContrast;
        const scale = Number(prefs?.fontScale || 1);

        html.classList.toggle("dark", dark);
        html.classList.toggle("high-contrast", hc);
        html.style.fontSize = `${16 * scale}px`;

        const lang = prefs?.language === "en" ? "en" : "es";
        i18n?.changeLanguage?.(lang);

        const current = JSON.parse(localStorage.getItem("app:settings") || "{}");
        const merged = {
            ...current,
            language: lang,
            darkMode: dark,
            fontScale: scale,
            highContrast: hc,
        };
        localStorage.setItem("app:settings", JSON.stringify(merged));
    } catch {
        // no-op
    }
}

async function fetchUserSettingsIfPossible(token) {
    try {
        const headers = { Accept: "application/json" };
        const init = { method: "GET", headers, credentials: "include" };
        if (token) init.headers = { ...headers, Authorization: `Bearer ${token}` };
        const rsp = await fetch(USER_SETTINGS_URL, init);
        if (!rsp.ok) return null;
        return await rsp.json();
    } catch {
        return null;
    }
}

export default function ChatPage({
    forceEmbed = false,
    avatarSrc = DEFAULT_BOT_AVATAR,
    title = "Asistente Tutor Virtual",
    connectFn,
    embedHeight = "560px",
    children,
}) {
    const { t, i18n } = useTranslation();
    const [params] = useSearchParams();
    const location = useLocation();

    const isEmbed = forceEmbed || params.get("embed") === "1";
    const isFullScreenRoute = /^\/(chat|widget|iframe\/chat)/.test(location.pathname);
    const wantFullScreen = isEmbed || isFullScreenRoute;

    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [status, setStatus] = useState("connecting");

    // Token invitado (si no hay)
    try {
        const existing = localStorage.getItem(STORAGE_KEYS.accessToken);
        if (!existing) {
            const guest = "guest-" + Math.random().toString(36).slice(2, 10);
            localStorage.setItem(STORAGE_KEYS.accessToken, guest);
        }
    } catch {
        // no-op
    }

    // Evitar navegación del iframe en modo embed
    useEffect(() => {
        if (!isEmbed) return;
        const onClick = (e) => {
            const a = e.target.closest?.("a");
            if (a && a.href && !a.href.startsWith("javascript:")) {
                e.preventDefault();
                e.stopPropagation();
            }
        };
        window.addEventListener("click", onClick, true);
        return () => window.removeEventListener("click", onClick, true);
    }, [isEmbed]);

    /* 🌐 Determinar tipo de conexión (health) */
    const defaultConnect = useMemo(() => {
        if (connectFn) return connectFn;
        if (TRANSPORT === "ws") {
            return () => connectWS({ wsUrl: RASA_WS_URL });
        }
        // conservamos tu firma (aunque connectChatHealth no requiera args)
        return () => connectChatHealth({ restUrl: CHAT_REST_URL, rasaHttpUrl: RASA_HTTP_URL });
    }, [connectFn]);

    const connect = useCallback(async () => {
        setStatus("connecting");
        let done = false;
        const watchdog = setTimeout(() => {
            if (!done) {
                console.warn("[ChatPage] watchdog: continúo con UI");
                setStatus("ready"); // permite ver la UI aunque el health tarde
            }
        }, 2500);

        try {
            if (defaultConnect) await defaultConnect();
            else await new Promise((r) => setTimeout(r, 600));
            done = true;
            clearTimeout(watchdog);
            setStatus("ready");
        } catch (e) {
            done = true;
            clearTimeout(watchdog);
            console.warn("[ChatPage] Health check falló:", e?.message || e);
            setStatus("error");
        }
    }, [defaultConnect]);

    // (Opcional) Pide token al host al montar en embed
    useEffect(() => {
        if (isEmbed) {
            try {
                window.parent?.postMessage({ type: "auth:request" }, "*");
            } catch { }
        }
    }, [isEmbed]);

    useEffect(() => {
        connect();
    }, [connect]);

    // Redirige a login si la app requiere auth y NO es embed
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

    // Aplicar preferencias de usuario cuando ready + autenticado
    useEffect(() => {
        if (status !== "ready") return;
        if (!isAuthenticated) return;
        let token = null;
        try {
            token = localStorage.getItem(STORAGE_KEYS.accessToken) || null;
        } catch { }
        (async () => {
            const prefs = await fetchUserSettingsIfPossible(token);
            if (prefs && typeof document !== "undefined") applyPrefsToDocument(prefs, i18n);
        })();
    }, [status, isAuthenticated, i18n]);

    // Mantener atributo lang en <html>
    useEffect(() => {
        try {
            const html = document.documentElement;
            const current = i18n.language?.startsWith("en") ? "en" : "es";
            if (html.getAttribute("lang") !== current) html.setAttribute("lang", current);
        } catch { }
    }, [i18n.language]);

    // Autoscroll al enfocar
    useEffect(() => {
        const el = document.querySelector(".chat-messages");
        if (!el) return;
        const onFocus = () => {
            try {
                el.scrollTop = el.scrollHeight;
            } catch { }
        };
        window.addEventListener("focusin", onFocus);
        return () => window.removeEventListener("focusin", onFocus);
    }, []);

    // Mensajes desde el host (tema, idioma, auth token)
    useEffect(() => {
        const handler = (e) => {
            const { data } = e;
            if (data?.type === "host:setTheme") {
                document.documentElement.classList.toggle("dark", data.theme === "dark");
            }
            if (data?.type === "host:setLanguage") {
                const lang = data.language?.startsWith("en") ? "en" : "es";
                i18n.changeLanguage(lang);
                document.documentElement.setAttribute("lang", lang);
            }
            if (data?.type === "auth:token" && data?.token) {
                try {
                    localStorage.setItem(STORAGE_KEYS.accessToken, data.token);
                } catch { }
            }
        };
        window.addEventListener("message", handler);
        return () => window.removeEventListener("message", handler);
    }, [i18n]);

    // Auto minimizar si viene en embed
    useEffect(() => {
        if (isEmbed && AUTO_MINIMIZE) {
            const timer = setTimeout(() => {
                window.parent?.postMessage({ type: "widget:toggle", action: "close" }, "*");
            }, 800);
            return () => clearTimeout(timer);
        }
    }, [isEmbed]);

    // Si requiere auth y no hay, volvemos a inicio (tu lógica intacta)
    if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
        navigate("/", { replace: true });
        return null;
    }

    // Layout según contexto
    const wrapperClass = wantFullScreen
        ? "p-0 h-screen flex flex-col"
        : "p-6 min-h-[70vh] flex flex-col";

    const bodyClass = wantFullScreen
        ? "flex-1 bg-white rounded-none border-0 shadow-none overflow-hidden"
        : "flex-1 bg-white rounded border shadow overflow-hidden";

    const wrapperStyle = isEmbed ? { height: embedHeight || "100vh" } : undefined;

    // Mostrar/ocultar la barra superior en EMBED
    const SHOW_EMBED_TOPBAR = true;

    return (
        <div className={wrapperClass} style={wrapperStyle}>
            {/* 🔹 Header fijo solo en modo embed (fuera del body visual) */}
            {isEmbed && SHOW_EMBED_TOPBAR && (
                <div
                    className="fixed top-0 left-0 w-full bg-slate-800 text-white p-2 text-sm flex justify-between items-center z-50"
                    role="region"
                    aria-label="Barra del chat embebido"
                >
                    <span>Tutor Virtual</span>
                    <button
                        onClick={() => window.parent?.postMessage({ type: "widget:toggle" }, "*")}
                        className="underline"
                        type="button"
                    >
                        ✕ Minimizar
                    </button>
                </div>
            )}

            {/* 🧩 Cabecera normal (no embed) */}
            {!isEmbed && (
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-indigo-600" />
                        <h1 className="text-2xl font-bold">{title}</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <ChatbotStatusMini status={status} />
                    </div>
                </div>
            )}

            {/* 💬 Cuerpo principal */}
            <div
                className={bodyClass}
                data-testid="chat-root"
                /* si es embed + topbar, deja espacio para el header fijo */
                style={isEmbed && SHOW_EMBED_TOPBAR ? { paddingTop: 36 } : undefined}
            >
                {status === "connecting" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6">
                        {/* Evitar avatar gigante en loader */}
                        <div style={{ maxWidth: 180 }}>
                            <ChatbotLoading avatarSrc={avatarSrc} label={t("chat.connecting")} />
                        </div>
                        <ChatbotStatusMini status="connecting" />
                    </div>
                )}

                {status === "error" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6 text-center">
                        <p className="text-gray-700">{t("chat.errorConnection")}</p>
                        <button
                            onClick={connect}
                            className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-100"
                            type="button"
                        >
                            <RefreshCw className="w-4 h-4" />
                            {t("chat.retry")}
                        </button>
                    </div>
                )}

                {status === "ready" && (
                    <div className="w-full h-full">
                        {/* Render directo del chat.
               - Web normal: /chat  (embed=false)
               - Embebido:    /chat?embed=1 (embed=true) */}
                        {children ?? <ChatUI embed={isEmbed} />}
                    </div>
                )}
            </div>
        </div>
    );
}
