// src/pages/ChatPage.jsx
import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { RefreshCw, AlertTriangle } from "lucide-react";
import ChatUI from "@/components/chat/ChatUI";
import ChatbotLoading from "@/components/ChatbotLoading";
import ChatbotStatusMini from "@/components/ChatbotStatusMini";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";
import { connectChatHealth } from "@/services/chat/health";
import { connectWS } from "@/services/chat/connectWS";
import Harness from "@/pages/Harness";
import { STORAGE_KEYS } from "@/lib/constants";
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";
const CHAT_REST_URL =
    import.meta.env.VITE_CHAT_REST_URL || `${API_BASE.replace(/\/$/, "")}/chat`;
const RASA_HTTP_URL =
    import.meta.env.VITE_RASA_REST_URL ||
    import.meta.env.VITE_RASA_HTTP ||
    "/rasa";
const RASA_WS_URL =
    import.meta.env.VITE_RASA_WS_URL || import.meta.env.VITE_RASA_WS || "/ws";

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
    } catch { }
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
    title = "Asistente Tutor Virtual",
    subtitle = "Tutor Virtual Zajuna · v7.3",
    connectFn,
    embedHeight = "560px",
    children,
}) {
    const { t, i18n } = useTranslation();
    const [params] = useSearchParams();
    const location = useLocation();

    const isEmbed = forceEmbed || params.get("embed") === "1";
    const isFullScreenRoute = /^\/(chat|widget|iframe\/chat)/.test(
        location.pathname
    );
    const wantFullScreen = isEmbed || isFullScreenRoute;

    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // Estados: "connecting" | "ready" | "ready-degraded"
    const [status, setStatus] = useState("connecting");
    const [degraded, setDegraded] = useState(false);

    // token invitado
    try {
        const existing = localStorage.getItem(STORAGE_KEYS.accessToken);
        if (!existing) {
            const guest = "guest-" + Math.random().toString(36).slice(2, 10);
            localStorage.setItem(STORAGE_KEYS.accessToken, guest);
        }
    } catch { }

    // bloquear navegación en embed
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

    /* health / conexión (NO bloquea el chat si falla → modo degradado) */
    const defaultConnect = useMemo(() => {
        if (connectFn) return connectFn;
        if (TRANSPORT === "ws")
            return () => connectWS({ wsUrl: RASA_WS_URL });
        return () =>
            connectChatHealth({ restUrl: CHAT_REST_URL, rasaHttpUrl: RASA_HTTP_URL });
    }, [connectFn]);

    const connect = useCallback(async () => {
        setStatus("connecting");
        setDegraded(false);

        // watchdog: si se demora, seguimos igual en ready
        let forced = false;
        const watchdog = setTimeout(() => {
            forced = true;
            setStatus("ready");
            setDegraded(true);
        }, 2500);

        try {
            if (defaultConnect) await defaultConnect();
            if (!forced) {
                clearTimeout(watchdog);
                setStatus("ready");
                setDegraded(false);
            }
        } catch (e) {
            clearTimeout(watchdog);
            console.warn(
                "[chat] Health falló, continuando en modo degradado:",
                e?.message || e
            );
            setStatus("ready");
            setDegraded(true);
        }
    }, [defaultConnect]);

    // pedir token al host si embed
    useEffect(() => {
        if (isEmbed) {
            try {
                window.parent?.postMessage?.({ type: "auth:request" }, "*");
            } catch { }
        }
    }, [isEmbed]);

    useEffect(() => {
        connect();
    }, [connect]);

    // auth requerida en modo no-embed
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

    // aplicar preferencias al estar listo
    useEffect(() => {
        if (status !== "ready" || !isAuthenticated) return;
        let token = null;
        try {
            token = localStorage.getItem(STORAGE_KEYS.accessToken) || null;
        } catch { }
        (async () => {
            const prefs = await fetchUserSettingsIfPossible(token);
            if (prefs && typeof document !== "undefined")
                applyPrefsToDocument(prefs, i18n);
        })();
    }, [status, isAuthenticated, i18n]);

    // lang en <html>
    useEffect(() => {
        try {
            const html = document.documentElement;
            const current = i18n.language?.startsWith("en") ? "en" : "es";
            if (html.getAttribute("lang") !== current)
                html.setAttribute("lang", current);
        } catch { }
    }, [i18n.language]);

    // autoscroll al enfocar
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

    // mensajes del host
    useEffect(() => {
        const handler = (e) => {
            const { data } = e;
            if (data?.type === "host:setTheme") {
                document.documentElement.classList.toggle(
                    "dark",
                    data.theme === "dark"
                );
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

    // auto minimizar en embed
    useEffect(() => {
        if (isEmbed && AUTO_MINIMIZE) {
            const timer = setTimeout(() => {
                window.parent?.postMessage(
                    { type: "widget:toggle", action: "close" },
                    "*"
                );
            }, 800);
            return () => clearTimeout(timer);
        }
    }, [isEmbed]);

    if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
        navigate("/", { replace: true });
        return null;
    }

    /* ------- Layout responsivo y alto completo ------- */
    const wrapperClass = wantFullScreen
        ? "p-0 min-h-[100dvh] flex flex-col"
        : "p-4 md:p-6 min-h-[90dvh] flex flex-col";
    const bodyClass =
        "flex-1 bg-white rounded border shadow overflow-hidden min-h-[60dvh]";

    const wrapperStyle = isEmbed ? { height: embedHeight || "100vh" } : undefined;

    const SHOW_EMBED_TOPBAR = true;

    return (
        <div className={wrapperClass} style={wrapperStyle}>
            {/* barra fija en embed */}
            {isEmbed && SHOW_EMBED_TOPBAR && (
                <div
                    className="fixed top-0 left-0 w-full bg-slate-800 text-white p-2 text-sm flex justify-between items-center z-50"
                    role="region"
                    aria-label="Barra del chat embebido"
                >
                    <span>
                        Este es un mecanismo de comunicación de soporte. Bienvenido
                        aprendiz
                    </span>
                    <button
                        onClick={() =>
                            window.parent?.postMessage({ type: "widget:toggle" }, "*")
                        }
                        className="underline"
                        type="button"
                    >
                        ✕ Minimizar
                    </button>
                </div>
            )}

            {/* NAVBAR (modo normal, no embed) */}
            {!isEmbed && (
                <header className="mb-3 md:mb-4">
                    <div className="max-w-5xl mx-auto w-full px-3 py-2 rounded-xl bg-indigo-700 text-white shadow-sm flex items-center justify-between gap-3">
                        {/* Botón salir / volver al inicio */}
                        <button
                            type="button"
                            onClick={() => navigate("/")}
                            className="inline-flex items-center gap-1 text-xs sm:text-sm px-3 py-1.5 rounded-full bg-indigo-800 hover:bg-indigo-900 border border-white/40 focus:outline-none focus:ring-2 focus:ring-white/60"
                        >
                            <span>←</span>
                            <span>Salir</span>
                        </button>

                        {/* Título + subtítulo centrado */}
                        <div className="flex flex-col items-center justify-center text-center flex-1 min-w-0">
                            <h1 className="text-sm sm:text-lg md:text-xl font-semibold tracking-tight text-gray-50 break-words">
                                {title}
                            </h1>
                            {subtitle ? (
                                <p className="mt-0.5 text-[11px] sm:text-xs text-indigo-100 truncate max-w-full">
                                    {subtitle}
                                </p>
                            ) : null}
                        </div>

                        {/* Estado del bot + Configuración a la derecha */}
                        <div className="flex items-center justify-end gap-2 min-w-[150px]">
                            <ChatbotStatusMini status={degraded ? "warning" : status} />
                            <ChatConfigMenu />
                        </div>
                    </div>

                    {/* Aviso de modo degradado debajo del navbar */}
                    {degraded && (
                        <div className="max-w-5xl mx-auto px-3 pt-1">
                            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 flex items-center gap-2 text-amber-700 text-xs sm:text-sm">
                                <AlertTriangle className="w-4 h-4" />
                                <span>
                                    Conexión en modo degradado. Si algo falla, inténtalo de nuevo.
                                </span>
                            </div>
                        </div>
                    )}
                </header>
            )}

            {/* CUERPO */}
            <div
                className={bodyClass}
                data-testid="chat-root"
                style={isEmbed && SHOW_EMBED_TOPBAR ? { paddingTop: 36 } : undefined}
            >
                {status === "connecting" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6">
                        <div style={{ maxWidth: 160 }}>
                            <ChatbotLoading
                                label={t("chat.connecting", "Conectando…")}
                            />
                        </div>
                        <ChatbotStatusMini status="connecting" />
                    </div>
                )}

                {status === "ready" && (
                    <div className="w-full h-full">
                        {children ?? <ChatUI embed={isEmbed} />}
                    </div>
                )}

                {SHOW_HARNESS && !isEmbed && status === "ready" ? (
                    <Harness />
                ) : null}
            </div>
        </div>
    );
}
