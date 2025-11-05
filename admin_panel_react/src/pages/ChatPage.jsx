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
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";

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

/* ---------- helpers de preferencias ---------- */
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

function HeaderAvatar({
    src = DEFAULT_BOT_AVATAR,
    size = 72,
    title = "Asistente Tutor Virtual",
    subtitle = "", // 👈 NUEVO
}) {
    const [err, setErr] = useState(false);
    return (
        <div className="flex flex-col items-center text-center">
            <div
                className="rounded-full overflow-hidden ring-2 ring-indigo-100 shadow-sm bg-white"
                style={{ width: size, height: size }}
                aria-hidden="true"
            >
                {err ? (
                    <div className="w-full h-full grid place-items-center bg-indigo-50">
                        <Bot className="w-7 h-7 text-indigo-600" />
                    </div>
                ) : (
                    <img
                        src={src}
                        alt="Avatar del asistente"
                        className="w-full h-full object-cover"
                        onError={() => setErr(true)}
                    />
                )}
            </div>

            <h1 className="mt-2 text-xl font-semibold text-gray-900">{title}</h1>
            {subtitle ? (
                <p className="mt-0.5 text-sm text-gray-500">{subtitle}</p>
            ) : null}
        </div>
    );
}

export default function ChatPage({
    forceEmbed = false,
    avatarSrc = DEFAULT_BOT_AVATAR,
    title = "Asistente Tutor Virtual",
    subtitle = "Tutor Virtual Zajuna · v7.3", // 👈 NUEVO (puedes cambiar el texto o dejar vacío "")
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

    /* health / conexión */
    const defaultConnect = useMemo(() => {
        if (connectFn) return connectFn;
        if (TRANSPORT === "ws") {
            return () => connectWS({ wsUrl: RASA_WS_URL });
        }
        return () => connectChatHealth({ restUrl: CHAT_REST_URL, rasaHttpUrl: RASA_HTTP_URL });
    }, [connectFn]);

    const connect = useCallback(async () => {
        setStatus("connecting");
        let done = false;
        const watchdog = setTimeout(() => {
            if (!done) {
                console.warn("[ChatPage] watchdog: continúo con UI");
                setStatus("ready");
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

    // pedir token al host si embed
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

    // auth requerida en modo no-embed
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

    // aplicar preferencias al estar listo
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

    // lang en <html>
    useEffect(() => {
        try {
            const html = document.documentElement;
            const current = i18n.language?.startsWith("en") ? "en" : "es";
            if (html.getAttribute("lang") !== current) html.setAttribute("lang", current);
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

    // auto minimizar en embed
    useEffect(() => {
        if (isEmbed && AUTO_MINIMIZE) {
            const timer = setTimeout(() => {
                window.parent?.postMessage({ type: "widget:toggle", action: "close" }, "*");
            }, 800);
            return () => clearTimeout(timer);
        }
    }, [isEmbed]);

    if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
        navigate("/", { replace: true });
        return null;
    }

    // layout
    const wrapperClass = wantFullScreen
        ? "p-0 h-screen flex flex-col"
        : "p-6 min-h-[70vh] flex flex-col";

    const bodyClass = wantFullScreen
        ? "flex-1 bg-white rounded-none border-0 shadow-none overflow-hidden"
        : "flex-1 bg-white rounded border shadow overflow-hidden";

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
                    <span>Este es un mecanismo de comunicación de soporte. Bienvenido aprendiz</span>
                    <button
                        onClick={() => window.parent?.postMessage({ type: "widget:toggle" }, "*")}
                        className="underline"
                        type="button"
                    >
                        ✕ Minimizar
                    </button>
                </div>
            )}

            {/* header normal (no embed) con AVATAR CENTRADO, tamaño 72px, y contenedor con max-width */}
            {!isEmbed && (
                <div className="mb-4">
                    {/* contenedor responsivo y centrado */}
                    <div className="max-w-4xl mx-auto w-full px-3">
                        <div className="grid grid-cols-3 items-center">
                            {/* izquierda (espaciador para centrar) */}
                            <div />

                            {/* centro: avatar + título */}
                            <div className="flex flex-col items-center justify-center">
                                <HeaderAvatar src={avatarSrc} size={72} title={title} subtitle={subtitle} />
                            </div>

                            {/* derecha: estado + menú */}
                            <div className="flex items-center justify-end gap-2">
                                <ChatbotStatusMini status={status} />
                                <ChatConfigMenu />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* cuerpo principal */}
            <div
                className={bodyClass}
                data-testid="chat-root"
                style={isEmbed && SHOW_EMBED_TOPBAR ? { paddingTop: 36 } : undefined}
            >
                {status === "connecting" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6">
                        {/* loader con avatar controlado */}
                        <div style={{ maxWidth: 160 }}>
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
                        {children ?? <ChatUI embed={isEmbed} />}
                    </div>
                )}
            </div>
        </div>
    );
}

