// src/components/chat/ChatUI.jsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Send, User as UserIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/context/AuthContext";
import { sendRasaMessage } from "@/services/chat/connectRasaRest";
import MicButton from "./MicButton";
import { useVirtualizer } from "@tanstack/react-virtual";
import "./ChatUI.css";

// Helpers
function getParentOrigin() { try { return new URL(document.referrer || "").origin; } catch { return window.location.origin; } }
function normalize(o) { return String(o || "").trim().replace(/\/+$/, ""); }
const envAllowed = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "").split(",").map(s => normalize(s)).filter(Boolean);
const BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const USER_AVATAR_FALLBACK = import.meta.env.VITE_USER_AVATAR || "/user-avatar.png";

// Avatares
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

// ChatUI completo
export default function ChatUI({ embed = false, placeholder = "Escribe un mensaje…" }) {
    const { user } = useAuth();
    const [messages, setMessages] = useState([{ id: "welcome", role: "bot", text: "¡Hola! Soy tu asistente. ¿En qué puedo ayudarte?" }]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [authToken, setAuthToken] = useState(null);
    const [typing, setTyping] = useState(false);
    const listRef = useRef(null);
    const userId = useMemo(() => user?.email || user?._id || null, [user]);
    const parentOrigin = useMemo(() => normalize(getParentOrigin()), []);
    const allowed = useMemo(() => envAllowed, []);
    const needAuth = embed || !user;

    // Virtualización con v4+
    const rowVirtualizer = useVirtualizer({
        count: messages.length + (typing ? 1 : 0),
        getScrollElement: () => listRef.current,
        estimateSize: () => 80,
        overscan: 5,
    });

    // Scroll inteligente
    const isScrolledToBottom = useRef(true);
    const scrollToBottom = () => {
        const el = listRef.current;
        if (!el) return;
        el.scrollTop = el.scrollHeight;
    };
    useEffect(() => {
        const el = listRef.current;
        const onScroll = () => {
            if (!el) return;
            const threshold = 50;
            isScrolledToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
        };
        el?.addEventListener("scroll", onScroll);
        return () => el?.removeEventListener("scroll", onScroll);
    }, []);
    useEffect(() => { if (isScrolledToBottom.current) scrollToBottom(); }, [messages, sending, typing]);

    function rspToArray(rsp) { return Array.isArray(rsp) ? rsp : rsp ? [rsp] : []; }

    // Append secuencial + indicador typing
    const appendBotMessages = useCallback(async (rsp) => {
        const items = [];
        rspToArray(rsp).forEach((item, idx) => {
            const baseId = `b-${Date.now()}-${idx}`;
            if (item.text) items.push({ id: `${baseId}-t`, role: "bot", text: item.text });
            if (item.image) items.push({ id: `${baseId}-img`, role: "bot", image: item.image });
            if (item.buttons) {
                items.push({
                    id: `${baseId}-btnGroup`,
                    role: "bot",
                    render: () => item.buttons.map((btn, i) => (
                        <div key={i} className="bot-interactive" onClick={() => handleActionClick(baseId, btn)}>
                            {btn.title}
                        </div>
                    ))
                });
            }
            if (item.quick_replies) {
                items.push({
                    id: `${baseId}-qrGroup`,
                    role: "bot",
                    render: () => item.quick_replies.map((qr, i) => (
                        <div key={i} className="bot-interactive" onClick={() => handleActionClick(baseId, qr)}>
                            {qr.title}
                        </div>
                    ))
                });
            }
            if (item.custom?.cards) {
                item.custom.cards.forEach((c, ci) => {
                    items.push({
                        id: `${baseId}-card-${ci}`,
                        role: "bot",
                        render: () => (
                            <div className="bot-interactive p-3 border rounded-md mb-2 cursor-pointer" onClick={() => handleActionClick(baseId, c)}>
                                {c.title || c.text || "Card"}
                            </div>
                        )
                    });
                });
            }
        });
        if (!items.length) items.push({ id: `b-${Date.now()}-empty`, role: "bot", text: "Hmm… no tengo una respuesta para eso." });

        setTyping(true);
        for (let i = 0; i < items.length; i++) {
            await new Promise(res => setTimeout(res, 150));
            setMessages(m => [...m, items[i]]);
        }
        setTyping(false);
    }, []);

    const sendToRasa = async ({ text, displayAs }) => {
        setError("");
        if (needAuth && !authToken) { window.parent?.postMessage({ type: "auth:needed" }, parentOrigin); setError("Necesitas iniciar sesión para continuar."); return; }
        setSending(true);
        setMessages(m => [...m, { id: `u-${Date.now()}`, role: "user", text: displayAs || text }]);
        setInput("");
        try {
            const rsp = await sendRasaMessage({ text, sender: userId || undefined, token: authToken || undefined });
            await appendBotMessages(rsp);
        } catch (e) { setError(e?.message || "Error al enviar el mensaje"); } finally { setSending(false); }
    };

    const handleSend = async () => { if (!input.trim() || sending) return; await sendToRasa({ text: input }); };
    const onKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } };
    const handleActionClick = async (groupId, { title, payload, url }) => { if (url) window.open(url, "_blank", "noopener,noreferrer"); if (!payload) return; await sendToRasa({ text: payload, displayAs: title }); };

    const BotRow = ({ children }) => <div className="flex items-start gap-2 justify-start animate-fade-slide">{children}</div>;
    const UserRow = ({ children }) => <div className="flex items-start gap-2 justify-end animate-fade-slide">{children}</div>;

    return (
        <div className="h-full flex flex-col">
            <div ref={listRef} className="flex-1 overflow-auto px-3 py-4">
                <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: "relative" }}>
                    {rowVirtualizer.getVirtualItems().map(virtualRow => {
                        const index = virtualRow.index;
                        const m = index < messages.length ? messages[index] : null;
                        const isTypingRow = typing && index === messages.length;
                        if (!m && !isTypingRow) return null;

                        const style = { position: "absolute", top: 0, left: 0, width: "100%", transform: `translateY(${virtualRow.start}px)` };
                        if (isTypingRow) {
                            return (
                                <div key="typing" style={style}>
                                    <BotRow>
                                        <BotAvatar size={28} />
                                        <div className="rounded-2xl px-3 py-2 max-w-[50%] text-sm break-words bg-gray-100 text-gray-800 animate-fade-slide">
                                            Escribiendo<span className="typing-dots">...</span>
                                        </div>
                                    </BotRow>
                                </div>
                            );
                        }

                        const isUser = m.role === "user";
                        const bubbleCls = isUser ? "bg-indigo-600 text-white" : "bg-gray-100 text-gray-800";
                        const commonCls = "rounded-2xl px-3 py-2 max-w-[75%] text-sm break-words";

                        const content = m.text ? (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                        ) : m.image ? (
                            <img src={m.image} alt="img" className="max-h-40 object-cover rounded-md" />
                        ) : m.render ? (
                            m.render()
                        ) : null;

                        return isUser ? (
                            <div key={m.id} style={style}><UserRow><div className={`${commonCls} ${bubbleCls}`}>{content}</div><UserAvatar user={user} size={28} /></UserRow></div>
                        ) : (
                            <div key={m.id} style={style}><BotRow><BotAvatar size={28} /><div className={`${commonCls} ${bubbleCls}`}>{content}</div></BotRow></div>
                        );
                    })}
                </div>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-center gap-2 p-2 border-t bg-gray-50">
                <MicButton onVoice={(p) => sendToRasa({ text: p })} disabled={sending} />
                <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKeyDown} placeholder={placeholder} className="flex-1 rounded-full border px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-indigo-300" disabled={sending} />
                <button type="submit" disabled={sending || !input.trim()} className="p-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center">
                    <Send className="w-4 h-4" />
                </button>
            </form>
        </div>
    );
}