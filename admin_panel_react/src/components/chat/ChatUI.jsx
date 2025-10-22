// src/components/chat/ChatUI.jsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Send, Loader2, User as UserIcon, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/context/AuthContext";
import { sendRasaMessage } from "@/services/chat/connectRasaRest";
import IconTooltip from "@/components/ui/IconTooltip";
import MicButton from "./MicButton";
import QuickActions from "./QuickActions";
import "./ChatUI.css";
// ————————————————————————————————
// Helpers
// ————————————————————————————————
function getParentOrigin() {
    try { const ref = document.referrer || ""; if (ref) return new URL(ref).origin; } catch { }
    return window.location.origin;
}
function normalize(o) { return String(o || "").trim().replace(/\/+$/, ""); }
const envAllowed = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "").split(",").map(s => normalize(s)).filter(Boolean);
const BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const USER_AVATAR_FALLBACK = import.meta.env.VITE_USER_AVATAR || "/user-avatar.png";
const SHOW_QUICK_ACTIONS = String(import.meta.env.VITE_SHOW_QUICK_ACTIONS ?? "true") === "true";

// ————————————————————————————————
// Avatares
// ————————————————————————————————
function BotAvatar({ size = 28 }) {
    const [err, setErr] = useState(false);
    return (
        <div className="shrink-0 rounded-full overflow-hidden border border-gray-200 bg-white flex items-center justify-center" style={{ width: size, height: size }}>
            {err ? <UserIcon className="w-4 h-4 text-indigo-600" /> : <img src={BOT_AVATAR} alt="Bot" className="w-full h-full object-cover" onError={() => setErr(true)} />}
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

// ————————————————————————————————
// ChatUI
// ————————————————————————————————
export default function ChatUI({ embed = false, placeholder = "Escribe un mensaje…" }) {
    const { user } = useAuth();
    const [messages, setMessages] = useState([{ id: "welcome", role: "bot", text: "¡Hola! Soy tu asistente. ¿En qué puedo ayudarte?" }]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [disabledActionGroups, setDisabledActionGroups] = useState(() => new Set());
    const [authToken, setAuthToken] = useState(null);
    const listRef = useRef(null);
    const unreadRef = useRef(0);
    const userId = useMemo(() => user?.email || user?._id || null, [user]);
    const parentOrigin = useMemo(() => normalize(getParentOrigin()), []);
    const allowed = useMemo(() => envAllowed, []);
    const isAllowed = useCallback(origin => normalize(origin) === parentOrigin || (allowed.length > 0 && allowed.includes(normalize(origin))), [parentOrigin, allowed]);
    const needAuth = embed || !user;

    const scrollToBottom = useCallback(() => { requestAnimationFrame(() => { const el = listRef.current; if (!el) return; el.scrollTop = el.scrollHeight + 256; }); }, []);
    useEffect(() => { scrollToBottom(); }, [messages, sending, scrollToBottom]);

    const postBadge = useCallback((count) => { try { if (window.parent && window.parent !== window) window.parent.postMessage({ type: "chat:badge", count }, parentOrigin); } catch { } }, [parentOrigin]);
    useEffect(() => { unreadRef.current = 0; postBadge(0); }, [postBadge]);

    useEffect(() => {
        const onMsg = (ev) => {
            if (!isAllowed(ev.origin)) return;
            const data = ev.data || {};
            if (data.type === "chat:visibility" && data.open) { unreadRef.current = 0; postBadge(0); }
            if (data.type === "auth:token" && data.token) setAuthToken(data.token);
        };
        window.addEventListener("message", onMsg);
        return () => window.removeEventListener("message", onMsg);
    }, [isAllowed, postBadge]);

    const appendBotMessages = useCallback((rsp) => {
        const out = [];
        rspToArray(rsp).forEach((item, idx) => {
            const baseId = `b-${Date.now()}-${idx}`;
            if (item.text) out.push({ id: `${baseId}-t`, role: "bot", text: item.text });
            if (item.image) out.push({ id: `${baseId}-img`, role: "bot", image: item.image });
            if (item.buttons) out.push({ id: `${baseId}-btn`, role: "bot", buttons: item.buttons });
            if (item.quick_replies) out.push({ id: `${baseId}-qr`, role: "bot", quickReplies: item.quick_replies });
            if (item.custom?.cards) item.custom.cards.forEach((c, ci) => out.push({ id: `${baseId}-card-${ci}`, role: "bot", card: c }));
        });
        if (!out.length) out.push({ id: `b-${Date.now()}-empty`, role: "bot", text: "Hmm… no tengo una respuesta para eso." });
        setMessages(m => [...m, ...out]);
        unreadRef.current += out.length; postBadge(unreadRef.current);
    }, [postBadge]);

    function rspToArray(rsp) { return Array.isArray(rsp) ? rsp : rsp ? [rsp] : []; }

    const sendToRasa = async ({ text, displayAs }) => {
        setError("");
        if (needAuth && !authToken) { window.parent?.postMessage({ type: "auth:needed" }, parentOrigin); setError("Necesitas iniciar sesión para continuar."); return; }
        setSending(true);
        setMessages(m => [...m, { id: `u-${Date.now()}`, role: "user", text: displayAs || text }]);
        setInput("");
        try {
            const rsp = await sendRasaMessage({ text, sender: userId || undefined, token: authToken || undefined });
            appendBotMessages(rsp);
        } catch (e) { setError(e?.message || "Error al enviar el mensaje"); }
        finally { setSending(false); scrollToBottom(); };
    };

    const handleSend = async () => { if (!input.trim() || sending) return; await sendToRasa({ text: input }); };
    const onKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } };
    const handleActionClick = async (groupId, { title, payload, url }) => { if (url) window.open(url, "_blank", "noopener,noreferrer"); if (!payload) return; setDisabledActionGroups(prev => new Set(prev).add(groupId)); await sendToRasa({ text: payload, displayAs: title }); };

    const BotRow = ({ children }) => <div className="flex items-start gap-2 justify-start">{children}</div>;
    const UserRow = ({ children }) => <div className="flex items-start gap-2 justify-end">{children}</div>;

    return (
        <div className="h-full flex flex-col">
            <div ref={listRef} className="flex-1 overflow-auto px-3 py-4">
                <div className="max-w-3xl mx-auto space-y-3">
                    {SHOW_QUICK_ACTIONS && <QuickActions onAction={(p, t) => sendToRasa({ text: p, displayAs: t })} show />}
                    {messages.map(m => {
                        const isUser = m.role === "user";
                        const bubbleCls = isUser ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-800";
                        const commonCls = "rounded-2xl px-3 py-2 max-w-[75%] text-sm break-words";

                        // Cards
                        if (m.card) return (
                            <BotRow key={m.id}>
                                <div className="rounded-xl border bg-white max-w-[75%] overflow-hidden">
                                    {m.card.image && <img src={m.card.image} alt={m.card.title} className="w-full h-40 object-cover" />}
                                    <div className="p-3">
                                        <div className="font-semibold">{m.card.title}</div>
                                        {m.card.subtitle && <div className="text-xs text-gray-500">{m.card.subtitle}</div>}
                                        {m.card.buttons && <div className="mt-2 flex flex-wrap gap-2">{m.card.buttons.map(b => (
                                            <button key={b.id} onClick={() => handleActionClick(m.id, b)} className="px-3 py-1.5 rounded-md border text-sm hover:bg-gray-50">{b.title}</button>
                                        ))}</div>}
                                    </div>
                                </div>
                            </BotRow>
                        );

                        // Quick replies / Buttons
                        if (m.buttons || m.quickReplies) return (
                            <BotRow key={m.id}>
                                <div className="rounded-2xl px-2 py-2 bg-gray-100 text-gray-800 max-w-[90%]">
                                    <div className="flex flex-wrap gap-2">
                                        {(m.buttons || m.quickReplies).map(q => (
                                            <button key={q.id} onClick={() => handleActionClick(m.id, q)} className="px-3 py-1.5 rounded-full border text-sm hover:bg-gray-50">{q.title}</button>
                                        ))}
                                    </div>
                                </div>
                            </BotRow>
                        );

                        // Texto / Markdown / Imagen inline
                        const content = m.text ? <ReactMarkdown remarkPlugins={[remarkGfm]} className="whitespace-pre-wrap break-words">{m.text}</ReactMarkdown>
                            : m.image && <div className="flex items-center gap-2"><a href={m.image} target="_blank" rel="noreferrer"><img src={m.image} alt="imagen" className="max-h-40 object-cover rounded-md" /></a></div>;

                        return isUser ? (
                            <UserRow key={m.id}>
                                <div className={commonCls + " " + bubbleCls}>{content}</div>
                                <UserAvatar user={user} size={28} />
                            </UserRow>
                        ) : (
                            <BotRow key={m.id}>
                                <BotAvatar size={28} />
                                <div className={commonCls + " " + bubbleCls}>{content}</div>
                            </BotRow>
                        );
                    })}
                    {sending && (
                        <BotRow>
                            <BotAvatar size={28} />
                            <div className="rounded-2xl px-3 py-2 bg-gray-100 text-gray-800 flex items-center gap-2 text-sm animate-pulse"> <Loader2 className="w-4 h-4 animate-spin" /> escribiendo… </div>
                        </BotRow>
                    )}
                    {error && <div className="text-xs text-red-500 mt-1">{error}</div>}
                </div>
            </div>

            <form onSubmit={e => { e.preventDefault(); handleSend(); }} className="flex items-center gap-2 p-2 border-t bg-gray-50">
                <MicButton onVoice={p => sendToRasa({ text: p })} disabled={sending} />
                <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKeyDown} placeholder={placeholder} className="flex-1 rounded-full border px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-indigo-300" disabled={sending} />
                <button type="submit" disabled={sending || !input.trim()} className="p-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center"><Send className="w-4 h-4" /></button>
            </form>
        </div>
    );
}
