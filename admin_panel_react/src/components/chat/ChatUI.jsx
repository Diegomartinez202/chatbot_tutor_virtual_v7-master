// src/components/chat/ChatUI.jsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Send, User as UserIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/context/AuthContext";
import MicButton from "./MicButton";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { STORAGE_KEYS } from "@/lib/constants";
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";
import "./ChatUI.css";
import QuickActions from "@/components/chat/QuickActions";
import { uploadVoiceBlob } from "@/services/voice/uploadVoice";

// ⛳️ nuevo helper REST con metadata.auth.hasToken
import { sendToRasaREST } from "./rasa/restClient.js";

// Evita doble saludo: aquí controlamos saludo inicial del cliente
const SEND_CLIENT_HELLO = true;

// Helpers
function getParentOrigin() {
    try { return new URL(document.referrer || "").origin; } catch { return window.location.origin; }
}
function normalize(o) { return String(o || "").trim().replace(/\/+$/, ""); }

const envAllowed = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "")
    .split(",").map((s) => normalize(s)).filter(Boolean);

const BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const USER_AVATAR_FALLBACK = import.meta.env.VITE_USER_AVATAR || "/user-avatar.png";

/*const LOCAL_ROUTES = Object.freeze({});

/*async function handleLocalPayload(/* { text, tChat, setMessages, sendToRasa } */) {
    // Siempre delegamos en Rasa.
    return false;
}

/* --- Avatares --- */
function BotAvatar({ size = 28 }) {
    const [err, setErr] = useState(false);
    return (
        <div className="shrink-0 rounded-full overflow-hidden border border-gray-200 bg-white flex items-center justify-center" style={{ width: size, height: size }}>
            {err ? <UserIcon className="w-4 h-4 text-indigo-600" /> : (
                <img src={BOT_AVATAR} alt="Bot" className="w-full h-full object-cover" onError={() => setErr(true)} />
            )}
        </div>
    );
}
function getInitials(source) {
    const s = String(source || "").trim();
    if (!s) return "U";
    const base = s.includes("@") ? s.split("@")[0] : s;
    const parts = base.replace(/[_\-\.]+/g, " ").split(" ").filter(Boolean);
    const a = (parts[0] || "").charAt(0);
    const b = (parts[1] || "").charAt(0);
    return (a + b).toUpperCase() || a.toUpperCase() || "U";
}
function UserAvatar({ user, size = 28 }) {
    const [err, setErr] = useState(false);
    const src = user?.avatarUrl || user?.photoUrl || user?.image || user?.photo || USER_AVATAR_FALLBACK || "";
    if (!src || err) {
        const initials = getInitials(user?.nombre || user?.name || user?.email);
        return (
            <div className="shrink-0 rounded-full border border-gray-200 bg-gray-100 text-gray-700 flex items-center justify-center font-semibold" style={{ width: size, height: size }}>
                {initials?.slice(0, 2) || <UserIcon className="w-4 h-4" />}
            </div>
        );
    }
    return <img src={src} alt={user?.nombre || user?.name || user?.email} className="w-full h-full object-cover rounded-full" onError={() => setErr(true)} />;
}

export default function ChatUI({ embed = false, placeholder = "Escribe tu mensaje…" }) {
    const { user } = useAuth();
    const { t: tChat } = useTranslation("chat");
    const { t: tConfig } = useTranslation("config");

    // ✅ senderId estable por sesión para Rasa
    const [senderId] = useState(() => {
        const k = "rasa:senderId";
        try {
            const existing = localStorage.getItem(k);
            if (existing) return existing;
            const id = "web-" + Math.random().toString(36).slice(2, 10);
            localStorage.setItem(k, id);
            return id;
        } catch {
            return "web-" + Math.random().toString(36).slice(2, 10);
        }
    });

    const storeToken = useAuthStore((s) => s.accessToken);
    const [authToken, setAuthToken] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [typing, setTyping] = useState(false);

    // Acciones rápidas visibles al inicio
    const [showQuick, setShowQuick] = useState(true);

    // Placeholders para compatibilidad
    const [hasShownSuggestions] = useState(false);
    const [hasSentFirstMessage, setHasSentFirstMessage] = useState(false);
    const appendFirstSuggestions = () => { }; 
    // Saludo inicial inmediato (solo cliente)
    useEffect(() => {
        if (SEND_CLIENT_HELLO) {
            setMessages([{
                id: "welcome",
                role: "bot",
                text: tChat("welcome", "¡Hola! Soy tu tutor virtual 🤖. ¿En qué puedo ayudarte hoy?"),
            }]);
        }
    }, [tChat]);

    // Token del store / localStorage
    useEffect(() => {
        if (storeToken) setAuthToken(storeToken);
        else {
            try {
                const ls = localStorage.getItem(STORAGE_KEYS.accessToken) || localStorage.getItem("zajuna_token");
                if (ls) setAuthToken(ls);
            } catch { }
        }
    }, [storeToken]);

    const userId = useMemo(() => user?.email || user?._id || null, [user]);
    const parentOrigin = useMemo(() => normalize(getParentOrigin()), []);

    // Detecta modo invitado en embed: /?embed=1&guest=1
    const urlParams = new URLSearchParams(window.location.search);
    const isGuestEmbed = urlParams.get("guest") === "1";

    // 🔐 Solo obliga login para intents que lo requieran
    function requiresAuthFor(text) {
        const t = String(text || "").trim();
        const NEED_AUTH = [
            "/mis_cursos",
            "/ver_progreso",
            "/estado_estudiante",
            "/tutor_asignado",
            "/ingreso_zajuna",
            "/faq_ingreso_privado",
            "/user_panel",
        ];
        return NEED_AUTH.includes(t);
    }

    // Bridge: recibe token del host
    useEffect(() => {
        if (!embed) return;
        const onMsg = (ev) => {
            try {
                const origin = normalize(ev.origin || "");
                if (envAllowed.length && !envAllowed.includes(origin)) return;
                const data = ev.data || {};
                if (data?.type === "auth:token" && data?.token) setAuthToken(String(data.token));
                if (data?.type === "host:open") { /* opcional */ }
                if (data?.type === "host:close") { /* opcional */ }
            } catch { }
        };
        window.addEventListener("message", onMsg);
        return () => window.removeEventListener("message", onMsg);
    }, [embed]);

    // Al cargar en embed, solicita token al host si existe sesión
    useEffect(() => {
        if (!embed) return;
        try { window.parent?.postMessage({ type: "auth:request" }, "*"); } catch { }
    }, [embed]);

    const rspToArray = (rsp) => (Array.isArray(rsp) ? rsp : rsp ? [rsp] : []);

    const appendBotMessages = useCallback(async (rsp) => {
        const items = [];
        rspToArray(rsp).forEach((item, idx) => {
            const baseId = `b-${Date.now()}-${idx}`;
            if (item.text) items.push({ id: `${baseId}-t`, role: "bot", text: item.text });
            if (item.image) items.push({ id: `${baseId}-img`, role: "bot", image: item.image });
            if (item.buttons) {
                items.push({
                    id: `${baseId}-btns`,
                    role: "bot",
                    render: () => (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {item.buttons.map((btn, i) => (
                                <button key={i} type="button" className="bot-interactive"
                                    onClick={() => handleActionClick(baseId, btn)}>
                                    {btn.title}
                                </button>
                            ))}
                        </div>
                    ),
                });
            }
            if (item.quick_replies) {
                items.push({
                    id: `${baseId}-qr`,
                    role: "bot",
                    render: () => (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {item.quick_replies.map((qr, i) => (
                                <button key={i} type="button" className="bot-interactive"
                                    onClick={() => handleActionClick(baseId, qr)}>
                                    {qr.title}
                                </button>
                            ))}
                        </div>
                    ),
                });
            }
        });
        if (!items.length) items.push({ id: `b-${Date.now()}-empty`, role: "bot", text: tChat("noResponse") });

        setTyping(true);
        for (let i = 0; i < items.length; i++) {
            await new Promise((r) => setTimeout(r, 140));
            setMessages((m) => [...m, items[i]]);
        }
        setTyping(false);

        try { window.parent?.postMessage({ type: "telemetry", event: "message_received" }, "*"); } catch { }
    }, [tChat]);

    /* --- sendToRasa con auth diferida --- */
    const sendToRasa = async ({ text, displayAs, isPayload = false }) => {
        setError("");
        try {
            const rsp = await sendRasaMessage({
                text,
                sender: userId || undefined,
                token: authToken || undefined,
            });
            await appendBotMessages(rsp);
        // 🔐 Solo exige auth si la acción lo requiere (y no hay token)
        if (embed && requiresAuthFor(text) && !authToken) {
            try { window.parent?.postMessage?.({ type: "auth:request" }, "*"); } catch { }
            setError(tChat("authRequired", "Para continuar, inicia sesión."));
            return;
        }

        // pinta el mensaje del usuario
        setSending(true);
        setMessages((m) => [...m, { id: `u-${Date.now()}`, role: "user", text: displayAs || text }]);
        setInput("");

        // oculta QuickActions al primer input/acción
        setShowQuick(false);

        // (Compat) sugerencias clásicas (no-op si no las usas)
        if (!isPayload && !hasShownSuggestions && hasSentFirstMessage) {
            appendFirstSuggestions();
        }

        try {
            window.parent?.postMessage?.({ type: "telemetry", event: "message_sent" }, "*");
        } catch { }

        try {
            // Si quisieras, aquí podrías renderizar algo local; por ahora todo lo maneja Rasa
            if (isPayload) {
                await handleLocalPayload({ text /*, tChat, setMessages, sendToRasa */ });
            }

            // ⛳️ LLAMADA ÚNICA: siempre via REST helper con metadata
            const rsp = await sendToRasaREST(senderId, text);
            await appendBotMessages(rsp);
        } catch (e) {
            setError(e?.message || tChat("errorSending"));
        } finally {
            setSending(false);
            if (!hasSentFirstMessage) setHasSentFirstMessage(true);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || sending) return;
        await sendToRasa({ text: input });
    };

    const onKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleActionClick = async (_groupId, { title, payload, url }) => {
        if (url) window.open(url, "_blank", "noopener,noreferrer");
        if (!payload) return;
        await sendToRasa({ text: payload, displayAs: title, isPayload: true });
    };

    const BotRow = ({ children }) => <div className="flex items-start gap-2 justify-start animate-fade-slide">{children}</div>;
    const UserRow = ({ children }) => <div className="flex items-start gap-2 justify-end animate-fade-slide">{children}</div>;

    return (
        <div className="h-full flex flex-col chat-container">
            {/* Header simple con Config a la derecha */}
            <div className="chat-header">
                <div className="chat-title">Asistente</div>

                {/* 👇 botón de cerrar/minimizar SOLO en embed */}
                {embed && (
                    <button
                        type="button"
                        className="ml-2 inline-flex items-center justify-center rounded px-2 py-1 text-sm border hover:bg-gray-50"
                        aria-label="Minimizar chat"
                        onClick={() => {
                            try { window.parent?.postMessage?.({ type: "widget:toggle" }, "*"); } catch { }
                        }}
                    >
                        ✕
                    </button>
                )}

                <div className="ml-auto">
                    <ChatConfigMenu />
                </div>
            </div>

            <div className="chat-messages px-3 py-4">
                {/* 🔹 QuickActions visible al inicio. Se oculta al primer input */}
                {showQuick && (
                    <QuickActions
                        show
                        onAction={(payload, title) => {
                            // pinta lo elegido
                            setMessages((m) => [...m, { id: `u-${Date.now()}`, role: "user", text: title || payload }]);
                            setShowQuick(false);
                            // envía el payload a Rasa (auth diferida aplica dentro de sendToRasa)
                            sendToRasa({ text: payload, displayAs: title, isPayload: true });
                        }}
                    />
                )}

                {messages.map((m) =>
                    m.role === "user" ? (
                        <UserRow key={m.id}>
                            <div className="bubble user">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                            </div>
                            <UserAvatar user={user} />
                        </UserRow>
                    ) : (
                        <BotRow key={m.id}>
                            <BotAvatar />
                            <div className="bubble bot">
                                {m.text && <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>}
                                {m.render && m.render()}
                            </div>
                        </BotRow>
                    )
                )}

                {typing && (
                    <BotRow>
                        <BotAvatar />
                        <div className="bubble bot">
                            {tChat("typing")}<span className="typing-dots" />
                        </div>
                    </BotRow>
                )}
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="chat-input-container">
                <MicButton
                    stt="auto"                              // o "none" si aún no tienes STT_URL configurado
                    onVoice={(text) => sendToRasa({ text })}
                    disabled={sending}
                />
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder={placeholder}
                    className="chat-input"
                    disabled={sending}
                />
                <button type="submit" disabled={sending || !input.trim()} className="send-button" aria-label="Enviar">
                    <Send className="w-4 h-4" />
                </button>
            </form>

            {error && (
                <div className="px-3 py-2 text-sm text-red-600" role="alert">
                    {error}
                </div>
            )}
        </div>
    );
}
