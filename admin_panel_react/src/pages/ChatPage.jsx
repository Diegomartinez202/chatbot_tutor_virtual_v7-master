// src/pages/ChatPage.jsx
import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Bot, RefreshCw } from "lucide-react";
import ChatUI from "@/components/chat/ChatUI";

import ChatbotLoading from "@/components/ChatbotLoading";
import ChatbotStatusMini from "@/components/ChatbotStatusMini";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";

import { connectChatHealth } from "@/services/chat/health";
import { connectWS } from "@/services/chat/connectWS";

import Harness from "@/pages/Harness";
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";
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
    (import.meta.env.VITE_USER_SETTINGS_URL && String(import.meta.env.VITE_USER_SETTINGS_URL).trim()) ||
    "/api/me/settings";

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
        /* no-op */
    }
}

async function fetchUserSettingsIfPossible(token) {
    try {
        const headers = { Accept: "application/json" };
        const init = {
            method: "GET",
            headers,
            credentials: "include",
        };
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
    title = "Asistente Tutor Virtual",
    connectFn,
    embedHeight = "560px",
    children,
}) {
    const { t, i18n } = useTranslation();
    const [params] = useSearchParams();
    const isEmbed = forceEmbed || params.get("embed") === "1";

    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [status, setStatus] = useState("connecting");

    // 🟢 Crear token invitado si no hay ninguno
    try {
        const existing = localStorage.getItem(STORAGE_KEYS.accessToken);
        if (!existing) {
            const guest = "guest-" + Math.random().toString(36).slice(2, 10);
            localStorage.setItem(STORAGE_KEYS.accessToken, guest);
        }
    } catch { }

    // 🔹 Listener para bloquear navegación externa dentro del iframe
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

    // 🔹 Determinar función de conexión
    const defaultConnect = useMemo(() => {
        if (connectFn) return connectFn;
        if (TRANSPORT === "ws") {
            return () => connectWS({ wsUrl: RASA_WS_URL });
        }
        return () => connectChatHealth({ restUrl: CHAT_REST_URL, rasaHttpUrl: RASA_HTTP_URL });
    }, [connectFn]);

    const connect = useCallback(async () => {
        setStatus("connecting");
        try {
            if (import.meta.env.MODE !== "production") {
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
            console.warn("[ChatPage] Health check falló:", e?.message || e);
            setStatus("error");
        }
    }, [defaultConnect]);

    useEffect(() => {
        connect();
    }, [connect]);

    // 🔒 Si requiere auth y no está autenticado (fuera de embed), redirige
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

    // 🔹 Cargar preferencias del usuario autenticado
    useEffect(() => {
        if (status !== "ready") return;
        if (!isAuthenticated) return;
        let token = null;
        try {
            token = localStorage.getItem(STORAGE_KEYS.accessToken) || null;
        } catch { }
        (async () => {
            const prefs = await fetchUserSettingsIfPossible(token);
            if (prefs && typeof document !== "undefined") {
                applyPrefsToDocument(prefs, i18n);
            }
        })();
    }, [status, isAuthenticated, i18n]);

    // 🔹 Mantener html lang sincronizado
    useEffect(() => {
        try {
            const html = document.documentElement;
            const current = i18n.language?.startsWith("en") ? "en" : "es";
            if (html.getAttribute("lang") !== current) {
                html.setAttribute("lang", current);
            }
        } catch { }
    }, [i18n.language]);

    // 🔹 Ajuste para teclado móvil
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

    // 🔹 Escucha mensajes del host (tema/idioma)
    useEffect(() => {
        const handler = (e) => {
            if (e.data?.type === "host:setTheme") {
                document.documentElement.classList.toggle("dark", e.data.theme === "dark");
            }
            if (e.data?.type === "host:setLanguage") {
                i18n.changeLanguage(e.data.language);
                document.documentElement.setAttribute("lang", e.data.language?.startsWith("en") ? "en" : "es");
            }
        };
        window.addEventListener("message", handler);
        return () => window.removeEventListener("message", handler);
    }, [i18n]);

    if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) return null;

    if (SHOW_HARNESS && !isEmbed) {
        return <Harness />;
    }

    const wrapperClass = isEmbed ? "p-0" : "p-6 min-h-[70vh] flex flex-col";
    const bodyClass = isEmbed ? "h-full" : "flex-1 bg-white rounded border shadow overflow-hidden";
    const wrapperStyle = isEmbed ? { height: embedHeight } : undefined;

    return (
        <div className={wrapperClass} style={wrapperStyle}>
            {/* 🟢 Header visible solo en modo embed */}
            {isEmbed && (
                <div className="fixed top-0 left-0 w-full bg-slate-800 text-white p-2 text-sm flex justify-between items-center z-50">
                    <span>Tutor Virtual</span>
                    <button
                        onClick={() => window.parent?.postMessage({ type: "host:close" }, "*")}
                        className="underline"
                    >
                        ✕ Cerrar
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
                        <ChatConfigMenu />
                    </div>
                </div>
            )}

            <div className={bodyClass} data-testid="chat-root">
                {status === "connecting" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6">
                        <ChatbotLoading avatarSrc={avatarSrc} label={t("chat.connecting")} />
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
