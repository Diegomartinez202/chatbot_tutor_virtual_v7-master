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
    subtitle = null,
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

   
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

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

   
    useEffect(() => {
        try {
            const html = document.documentElement;
            const current = i18n.language?.startsWith("en") ? "en" : "es";
            if (html.getAttribute("lang") !== current)
                html.setAttribute("lang", current);
        } catch { }
    }, [i18n.language]);

 
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

    const wrapperClass = wantFullScreen
        ? "p-0 h-screen flex flex-col overflow-hidden min-h-0"
        : "p-4 md:p-6 min-h-screen flex flex-col min-h-0";

    const bodyClass = wantFullScreen
        ? "flex-1 flex flex-col overflow-hidden min-h-0"  
        : "flex-1 bg-white rounded border shadow overflow-hidden min-h-[60dvh] min-h-0";

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
                    <div
                        className="
        max-w-5xl mx-auto w-full px-3 py-2 rounded-xl
        bg-indigo-700 text-white shadow-sm
        flex items-center justify-between gap-3
      "
                    >
                        {/* Configuración (aquí dentro ya tienes la opción 'Salir del chat') */}
                        <div className="flex items-center gap-2">
                            <ChatConfigMenu />
                        </div>

                        {/* Título centrado */}
                        <div className="flex flex-col items-center justify-center text-center flex-1 min-w-0">
                            <h1
                                className="
            font-semibold tracking-tight text-gray-50 break-words
            text-[clamp(1.1rem,3.6vw,1.8rem)]
          "
                            >
                                {title}
                            </h1>
                        </div>

                        {/* Estado del bot a la derecha */}
                        <div className="flex items-center justify-end">
                            <ChatbotStatusMini
                                status={degraded ? "warning" : status}
                                sizeClass="
            w-8 h-8
            sm:w-9 sm:h-9
            md:w-10 md:h-10
            lg:w-11 lg:h-11
            xl:w-12 xl:h-12
          "
                                className="shrink-0"
                            />
                        </div>
                    </div>

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
                    <div className="w-full h-full flex flex-col items-center justify-center gap-4 p-6">
                        <div className="flex items-center justify-center w-full">
                            <div className="max-w-[220px] sm:max-w-[260px] md:max-w-[300px]">
                                <ChatbotLoading
                                    label={t("chat.connecting", "Conectando…")}
                                />
                            </div>
                        </div>

                        {/* mini estado debajo, pequeñito */}
                        <ChatbotStatusMini
                            status="connecting"
                            sizeClass="w-7 h-7 sm:w-8 sm:h-8 md:w-9 md:h-9"
                        />
                    </div>
                )}

                {status === "ready" && (
                    <div className="w-full h-full flex justify-center">
                        {/* Contenedor del bot: ancho máximo y layout vertical */}
                        <div
                            className="
        w-full
        max-w-md          /* ancho tipo móvil */
        md:max-w-lg
        h-full            /* 👈 ocupa todo el alto del body */
        flex flex-col
        bg-[#050816]
      "
                        >
                            {children ?? <ChatUI embed={isEmbed} />}
                        </div>
                    </div>
                )}

                {SHOW_HARNESS && !isEmbed && status === "ready" ? (
                    <Harness />
                ) : null}
            </div>
        </div>
    );
}
