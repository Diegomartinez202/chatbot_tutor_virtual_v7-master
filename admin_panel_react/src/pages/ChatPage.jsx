// src/pages/ChatPage.jsx
import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Bot, RefreshCw } from "lucide-react";
import ChatUI from "@/components/chat/ChatUI";

import ChatbotLoading from "@/components/ChatbotLoading";
import ChatbotStatusMini from "@/components/ChatbotStatusMini";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next"; // 🟢 i18n hook agregado

// Health universal (REST/WS)
import { connectChatHealth } from "@/services/chat/health";
import { connectWS } from "@/services/chat/connectWS";

import Harness from "@/pages/Harness";
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";
import { STORAGE_KEYS } from "@/lib/constants";

const API_BASE =
    import.meta.env.VITE_API_BASE || "/api";

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

// 🔗 Endpoint de preferencias de usuario (lectura inicial)
const USER_SETTINGS_URL =
    (import.meta.env.VITE_USER_SETTINGS_URL && String(import.meta.env.VITE_USER_SETTINGS_URL).trim()) ||
    "/api/me/settings";

// Helpers
function applyPrefsToDocument(prefs, i18n) {
    try {
        const html = document.documentElement;
        const dark = prefs?.theme === "dark";
        const hc = !!prefs?.highContrast;
        const scale = Number(prefs?.fontScale || 1);

        html.classList.toggle("dark", dark);
        html.classList.toggle("high-contrast", hc);
        html.style.fontSize = `${16 * scale}px`;

        const lang = (prefs?.language === "en" ? "en" : "es");
        i18n?.changeLanguage?.(lang);

        // Sincroniza con SettingsPanel/localStorage
        const current = JSON.parse(localStorage.getItem("app:settings") || "{}");
        const merged = {
            ...current,
            language: lang,
            darkMode: dark,
            fontScale: scale,
            highContrast: hc,
        };
        localStorage.setItem("app:settings", JSON.stringify(merged));
    } catch { /* no-op */ }
}
function applyPrefsToDocument(prefs, i18n) {
    try {
        const html = document.documentElement;
        const dark = prefs?.theme === "dark";
        const hc = !!prefs?.highContrast;
        const scale = Number(prefs?.fontScale || 1);

        html.classList.toggle("dark", dark);
        html.classList.toggle("high-contrast", hc);
        html.style.fontSize = `${16 * scale}px`;

        const lang = (prefs?.language === "en" ? "en" : "es");
        i18n?.changeLanguage?.(lang);
        // 👇 adicional
        html.setAttribute("lang", lang);

        const current = JSON.parse(localStorage.getItem("app:settings") || "{}");
        const merged = { ...current, language: lang, darkMode: dark, fontScale: scale, highContrast: hc };
        localStorage.setItem("app:settings", JSON.stringify(merged));
    } catch { /* no-op */ }
}

async function fetchUserSettingsIfPossible(token) {
    try {
        const headers = { "Accept": "application/json" };
        const init = {
            method: "GET",
            headers,
            credentials: "include", // cookie HttpOnly si aplica
        };
        // Adjuntar Authorization si tenemos token en LS
        if (token) {
            init.headers = { ...headers, Authorization: `Bearer ${token}` };
        }

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
    title = "Asistente",
    connectFn,
    embedHeight = "560px",
    children,
}) {
    const { t, i18n } = useTranslation(); // i18n
    const [params] = useSearchParams();
    const isEmbed = forceEmbed || params.get("embed") === "1";

    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    const [status, setStatus] = useState("connecting"); // connecting | ready | error

    // Por defecto: valida WS si TRANSPORT=ws; de lo contrario health universal
    const defaultConnect = useMemo(() => {
        if (connectFn) return connectFn;
        if (TRANSPORT === "ws") {
            return () => connectWS({ wsUrl: RASA_WS_URL });
        }
        return () => connectChatHealth({ restUrl: CHAT_REST_URL, rasaHttpUrl: RASA_HTTP_URL });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [connectFn, TRANSPORT]);

    const connect = useCallback(async () => {
        setStatus("connecting");
        try {
            if (import.meta.env.MODE !== "production") {
                // eslint-disable-next-line no-console
                console.info(
                    "[ChatPage] mode=%s | REST=%s | RASA_HTTP=%s | WS=%s",
                    TRANSPORT.toUpperCase(),
                    CHAT_REST_URL,
                    RASA_HTTP_URL,
                    RASA_WS_URL
                );
            }

            if (defaultConnect) {
                await defaultConnect();
            } else {
                await new Promise((r) => setTimeout(r, 600));
            }
            setStatus("ready");
        } catch (e) {
            // eslint-disable-next-line no-console
            console.warn("[ChatPage] Health check falló:", e?.message || e);
            setStatus("error");
        }
    }, [defaultConnect]);

    useEffect(() => { connect(); }, [connect]);

    // 🔒 Redirección a login si así lo exige tu configuración (no en embed)
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

    // 🟢 Al estar READY y si el usuario está autenticado, lee y aplica preferencias del backend
    useEffect(() => {
        if (status !== "ready") return;
        if (!isAuthenticated) return;

        // Token LS opcional por si usas Authorization en vez (o además) de cookie HttpOnly
        let token = null;
        try {
            token = localStorage.getItem(STORAGE_KEYS.accessToken) || null;
        } catch { /* no-op */ }

        (async () => {
            const prefs = await fetchUserSettingsIfPossible(token);
            if (prefs && typeof document !== "undefined") {
                applyPrefsToDocument(prefs, i18n);
            }
        })();
    }, [status, isAuthenticated, i18n]);

    if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) return null;

    if (SHOW_HARNESS && !isEmbed) {
        return <Harness />;
    }
    // Mantener <html lang="..."> sincronizado con i18n
    useEffect(() => {
        try {
            const html = document.documentElement;
            const current = i18n.language?.startsWith("en") ? "en" : "es";
            if (html.getAttribute("lang") !== current) {
                html.setAttribute("lang", current);
            }
        } catch { }
    }, [i18n.language]);
    // Evita reflows agresivos al abrir el teclado virtual (móvil)
    useEffect(() => {
        const el = document.querySelector(".chat-messages");
        if (!el) return;
        const onFocus = () => { try { el.scrollTop = el.scrollHeight; } catch { } };
        window.addEventListener("focusin", onFocus);
        return () => window.removeEventListener("focusin", onFocus);
    }, []);

    const wrapperClass = isEmbed ? "p-0" : "p-6 min-h-[70vh] flex flex-col";
    const bodyClass = isEmbed ? "h-full" : "flex-1 bg-white rounded border shadow overflow-hidden";
    const wrapperStyle = isEmbed ? { height: embedHeight } : undefined;

    return (
        <div className={wrapperClass} style={wrapperStyle}>
            {!isEmbed && (
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-indigo-600" />
                        <h1 className="text-2xl font-bold">{title}</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <ChatbotStatusMini status={status} />
                        <ChatConfigMenu />
                    </div>
                </div>
            )}

            <div className={bodyClass} data-testid="chat-root">
                {status === "connecting" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6">
                        <ChatbotLoading
                            avatarSrc={avatarSrc}
                            label={t("chat.connecting")}
                        />
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

/* Ejemplos:
   <ChatPage />
   <ChatPage connectFn={() => connectWS({ wsUrl: import.meta.env.VITE_RASA_WS_URL })} />
   <ChatPage forceEmbed embedHeight="100vh" />
*/
