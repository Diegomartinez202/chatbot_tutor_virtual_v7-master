// src/components/chat/ChatUI.jsx
import React, {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import {
    Send,
    Loader2,
    AlertCircle,
    Image as ImgIcon,
    ExternalLink,
    User as UserIcon,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { sendRasaMessage } from "@/services/chat/connectRasaRest";
import IconTooltip from "@/components/ui/IconTooltip";
import MicButton from "./MicButton";
import QuickActions from "./QuickActions";

// ————————————————————————————————
// Helpers de origen seguro (parentOrigin + normalización)
// ————————————————————————————————
function getParentOrigin() {
    try {
        const ref = document.referrer || "";
        if (ref) return new URL(ref).origin;
    } catch { }
    return window.location.origin;
}
function normalize(o) {
    return String(o || "").trim().replace(/\/+$/, "");
}
const envAllowed = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "")
    .split(",")
    .map((s) => normalize(s))
    .filter(Boolean);

// Avatares configurables (public/… o ENV)
const BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const USER_AVATAR_FALLBACK =
    import.meta.env.VITE_USER_AVATAR ||
    import.meta.env.VITE_USER_AVATAR_DEFAULT ||
    "/user-avatar.png";

// Flag para mostrar/ocultar Acciones rápidas
const SHOW_QUICK_ACTIONS =
    String(import.meta.env.VITE_SHOW_QUICK_ACTIONS ?? "true") === "true";

// ————————————————————————————————
// Componentes de avatar
// ————————————————————————————————
function BotAvatar({ size = 28 }) {
    const [err, setErr] = useState(false);
    return (
        <div
            className="shrink-0 rounded-full overflow-hidden border border-gray-200 bg-white flex items-center justify-center"
            style={{ width: size, height: size }}
            aria-hidden="true"
        >
            {err ? (
                <svg viewBox="0 0 24 24" className="w-4 h-4 text-indigo-600" fill="currentColor">
                    <path d="M12 2a3 3 0 0 1 3 3v1h2a3 3 0 0 1 3 3v3a5 5 0 0 1-4 4.9V19a3 3 0 0 1-3 3h-4a3 3 0 0 1-3-3v-2.1A5 5 0 0 1 3 12V9a3 3 0 0 1 3-3h2V5a3 3 0 0 1 3-3Z" />
                </svg>
            ) : (
                <img
                    src={BOT_AVATAR}
                    alt="Bot"
                    className="w-full h-full object-cover"
                    onError={() => setErr(true)}
                    loading="eager"
                />
            )}
        </div>
    );
}

function getInitials(source) {
    const s = String(source || "").trim();
    if (!s) return "U";
    const base = s.includes("@") ? s.split("@")[0] : s;
    const parts = base
        .replace(/[_\-\.]+/g, " ")
        .split(" ")
        .filter(Boolean);
    const a = (parts[0] || "").charAt(0);
    const b = (parts[1] || "").charAt(0);
    return (a + b).toUpperCase() || a.toUpperCase() || "U";
}

function UserAvatar({ user, size = 28 }) {
    const [err, setErr] = useState(false);
    const src =
        user?.avatarUrl ||
        user?.photoUrl ||
        user?.image ||
        user?.photo ||
        user?.avatar ||
        USER_AVATAR_FALLBACK ||
        "";

    if (!src || err) {
        const initials = getInitials(user?.nombre || user?.name || user?.email);
        return (
            <div
                className="shrink-0 rounded-full border border-gray-200 bg-gray-100 text-gray-700 flex items-center justify-center font-semibold"
                style={{ width: size, height: size }}
                aria-hidden="true"
                title={user?.email || user?.nombre || user?.name || "Usuario"}
            >
                {initials?.trim() ? initials.slice(0, 2) : <UserIcon className="w-4 h-4" />}
            </div>
        );
    }

    return (
        <div
            className="shrink-0 rounded-full overflow-hidden border border-gray-200 bg-white flex items-center justify-center"
            style={{ width: size, height: size }}
            aria-hidden="true"
        >
            <img
                src={src}
                alt={user?.email || user?.nombre || user?.name || "Usuario"}
                className="w-full h-full object-cover"
                onError={() => setErr(true)}
                loading="eager"
            />
        </div>
    );
}

// ————————————————————————————————
// Chat UI
// ————————————————————————————————
export default function ChatUI({
    embed = false,
    placeholder = "Escribe un mensaje…",
}) {
    const { user } = useAuth();

    const [messages, setMessages] = useState([
        {
            id: "welcome",
            role: "bot",
            text: "¡Hola! Soy tu asistente. ¿En qué puedo ayudarte?",
        },
    ]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [disabledActionGroups, setDisabledActionGroups] = useState(
        () => new Set()
    );

    // 🔐 Token recibido vía postMessage (launcher → iframe)
    const [authToken, setAuthToken] = useState(null);

    const listRef = useRef(null);
    const unreadRef = useRef(0);

    const userId = useMemo(() => user?.email || user?._id || null, [user]);

    // Origen robusto del parent + whitelist desde ENV
    const parentOrigin = useMemo(() => normalize(getParentOrigin()), []);
    const allowed = useMemo(() => envAllowed, []);
    const isAllowed = useCallback(
        (origin) =>
            normalize(origin) === parentOrigin ||
            (allowed.length > 0 && allowed.includes(normalize(origin))),
        [parentOrigin, allowed]
    );

    const scrollToBottom = useCallback(() => {
        requestAnimationFrame(() => {
            const el = listRef.current;
            if (!el) return;
            el.scrollTop = el.scrollHeight + 256;
        });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, sending, scrollToBottom]);

    // 🔔 avisar al host (launcher) del conteo de no leídos
    const postBadge = useCallback(
        (count) => {
            try {
                if (typeof window !== "undefined" && window.parent && window.parent !== window) {
                    window.parent.postMessage({ type: "chat:badge", count }, parentOrigin);
                }
            } catch { }
        },
        [parentOrigin]
    );

    // Al montar: reset badge
    useEffect(() => {
        unreadRef.current = 0;
        postBadge(0);
    }, [postBadge]);

    // Resetear a 0 cuando el host abre el panel + recibir token
    useEffect(() => {
        const onMsg = (ev) => {
            if (!isAllowed(ev.origin)) return;
            const data = ev.data || {};
            if (data.type === "chat:visibility" && data.open === true) {
                unreadRef.current = 0;
                postBadge(0);
            }
            if (
                data.type === "auth:token" &&
                typeof data.token === "string" &&
                data.token.length > 0
            ) {
                setAuthToken(data.token);
                setError("");
            }
        };
        window.addEventListener("message", onMsg);
        return () => window.removeEventListener("message", onMsg);
    }, [isAllowed, postBadge]);

    // Normalizar respuesta Rasa → UI
    const normalizeRasaItems = (rsp) => {
        const out = [];
        (rsp || []).forEach((item, idx) => {
            const baseId = `b-${Date.now()}-${idx}`;

            if (item.text) out.push({ id: `${baseId}-t`, role: "bot", text: item.text });
            if (item.image) out.push({ id: `${baseId}-img`, role: "bot", image: item.image });

            if (Array.isArray(item.buttons) && item.buttons.length) {
                out.push({
                    id: `${baseId}-btns`,
                    role: "bot",
                    buttons: item.buttons.map((b, i) => ({
                        id: `${baseId}-btn-${i}`,
                        title: b.title || b.payload || "Opción",
                        payload: b.payload || b.title || "",
                    })),
                });
            }

            if (Array.isArray(item.quick_replies) && item.quick_replies.length) {
                out.push({
                    id: `${baseId}-qr`,
                    role: "bot",
                    quickReplies: item.quick_replies.map((q, i) => ({
                        id: `${baseId}-qr-${i}`,
                        title: q.title || q.payload || "Opción",
                        payload: q.payload || q.title || "",
                    })),
                });
            }

            const c = item.custom;
            if (c && typeof c === "object") {
                // Single card
                if (c.type === "card" || c.card) {
                    const card = c.card || c;
                    out.push({
                        id: `${baseId}-card`,
                        role: "bot",
                        card: {
                            title: card.title || "Tarjeta",
                            subtitle: card.subtitle || card.subtitle_text || "",
                            image: card.image || card.image_url || "",
                            buttons: (card.buttons || []).map((b, i) => ({
                                id: `${baseId}-card-btn-${i}`,
                                title: b.title || b.payload || "Abrir",
                                payload: b.payload || b.title || "",
                                url: b.url || b.link || "",
                            })),
                        },
                    });
                }
                // Multiple cards
                if (Array.isArray(c.cards)) {
                    c.cards.forEach((card, ci) => {
                        out.push({
                            id: `${baseId}-card-${ci}`,
                            role: "bot",
                            card: {
                                title: card.title || "Tarjeta",
                                subtitle: card.subtitle || "",
                                image: card.image || "",
                                buttons: (card.buttons || []).map((b, i) => ({
                                    id: `${baseId}-card-${ci}-btn-${i}`,
                                    title: b.title || b.payload || "Abrir",
                                    payload: b.payload || b.title || "",
                                    url: b.url || "",
                                })),
                            },
                        });
                    });
                }
            }
        });

        if (!out.length) {
            out.push({
                id: `b-${Date.now()}-empty`,
                role: "bot",
                text: "Hmm… no tengo una respuesta para eso. ¿Puedes reformular?",
            });
        }
        return out;
    };

    // Acepta array o objeto
    function rspToArray(rsp) {
        return Array.isArray(rsp) ? rsp : rsp ? [rsp] : [];
    }

    // 🔐 Política:
    const needAuth = embed || !user;

    // Helpers expuestos al MicButton
    const appendUserMessage = useCallback((text) => {
        const t = String(text || "").trim();
        if (!t) return;
        const userMsg = { id: `u-${Date.now()}`, role: "user", text: t };
        setMessages((m) => [...m, userMsg]);
    }, []);

    const appendBotMessages = useCallback(
        (rasaItemsArray) => {
            const botMsgs = normalizeRasaItems(rspToArray(rasaItemsArray));
            setMessages((m) => [...m, ...botMsgs]);
            const inc = botMsgs.length || 1;
            unreadRef.current = Math.max(0, unreadRef.current + inc);
            postBadge(unreadRef.current);
        },
        [postBadge]
    );

    // Pipeline → Rasa (con gate de auth)
    const sendToRasa = async ({ text, displayAs }) => {
        setError("");

        if (needAuth && !authToken && window.parent && window.parent !== window) {
            try {
                window.parent.postMessage({ type: "auth:needed" }, parentOrigin);
            } catch { }
            setError("Necesitas iniciar sesión para continuar.");
            return;
        }

        setSending(true);

        const userMsg = { id: `u-${Date.now()}`, role: "user", text: displayAs || text };
        setMessages((m) => [...m, userMsg]);
        setInput("");

        try {
            const rsp = await sendRasaMessage({
                text,
                sender: userId || undefined,
                metadata: { url: typeof location !== "undefined" ? location.href : undefined },
                token: authToken || undefined,
            });
            const botMsgs = normalizeRasaItems(rspToArray(rsp));
            setMessages((m) => [...m, ...botMsgs]);

            const inc = botMsgs.length || 1;
            unreadRef.current = Math.max(0, unreadRef.current + inc);
            postBadge(unreadRef.current);
        } catch (e) {
            // eslint-disable-next-line no-console
            console.error(e);
            setError(e?.message || "Error al enviar el mensaje");
            setMessages((m) => [
                ...m,
                {
                    id: `b-${Date.now()}-err`,
                    role: "bot",
                    text: "Ocurrió un error al contactar al asistente. Intenta nuevamente.",
                },
            ]);
        } finally {
            setSending(false);
        }
    };

    const handleSend = async () => {
        const text = input.trim();
        if (!text || sending) return;
        await sendToRasa({ text });
    };

    const onKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleActionClick = async (groupId, { title, payload, url }) => {
        if (url) window.open(url, "_blank", "noopener,noreferrer");
        if (!payload) return;
        setDisabledActionGroups((prev) => new Set(prev).add(groupId));
        await sendToRasa({ text: payload, displayAs: title });
    };

    // helpers de fila bot/usuario con avatar
    const BotRow = ({ children, testid }) => (
        <div className="flex items-start gap-2 justify-start" data-testid={testid}>
            <BotAvatar />
            {children}
        </div>
    );
    const UserRow = ({ children, testid }) => (
        <div className="flex items-start gap-2 justify-end" data-testid={testid}>
            {children}
            <UserAvatar user={user} />
        </div>
    );

    const meLabel = user?.email || user?.nombre || user?.name || "Tu cuenta";

    // persona/lang para el MicButton (audio)
    const qs = new URLSearchParams(
        typeof window !== "undefined" ? window.location.search : ""
    );
    const personaFromQS = qs.get("persona") || null;
    const langFromQS = qs.get("lang") || "es";

    // ✅ NUEVO: onSubmit para el form del composer
    const onSubmitComposer = useCallback(
        (e) => {
            e.preventDefault();
            if (!sending && input.trim()) {
                handleSend();
            }
        },
        [sending, input]
    );

    // Accionador para QuickActions → reusa pipeline del chat
    const handleQuickAction = useCallback(
        (payload, title) => {
            if (!payload) return;
            sendToRasa({ text: payload, displayAs: title });
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        []
    );

    return (
        <div
            className={embed ? "h-full flex flex-col" : "h-full flex flex-col bg-white"}
            data-testid="chat-ui"
        >
            {/* Mensajes */}
            <div
                ref={listRef}
                className={"flex-1 overflow-auto px-3 " + (embed ? "py-2" : "py-4 bg-white")}
                data-testid="chat-messages"
                aria-live="polite"
            >
                <div className="max-w-3xl mx-auto space-y-3">
                    {/* Panel de acciones rápidas */}
                    {SHOW_QUICK_ACTIONS && (
                        <QuickActions onAction={handleQuickAction} show={true} />
                    )}

                    {messages.map((m) => {
                        const isUser = m.role === "user";
                        const bubbleCls = isUser
                            ? "bg-indigo-600 text-white"
                            : "bg-gray-100 text-gray-800";
                        const commonCls = "rounded-2xl px-3 py-2 max-w-[75%] text-sm";

                        // Card
                        if (m.card) {
                            const gId = m.id;
                            const isDisabled = disabledActionGroups.has(gId);
                            return (
                                <BotRow key={m.id} testid="msg-bot">
                                    <div
                                        className="rounded-xl border bg-white text-gray-800 max-w-[75%] overflow-hidden"
                                        data-testid="msg-card"
                                    >
                                        {m.card.image ? (
                                            <img
                                                src={m.card.image}
                                                alt={m.card.title || "card"}
                                                className="w-full h-40 object-cover"
                                                loading="lazy"
                                            />
                                        ) : null}
                                        <div className="p-3">
                                            <div className="font-semibold">{m.card.title}</div>
                                            {m.card.subtitle ? (
                                                <div className="text-xs text-gray-500 mt-0.5">{m.card.subtitle}</div>
                                            ) : null}
                                            {!!(m.card.buttons || []).length && (
                                                <div className="mt-3 flex flex-wrap gap-2">
                                                    {m.card.buttons.map((b) => (
                                                        <IconTooltip key={b.id} label={b.payload || b.url || "Acción"} side="top">
                                                            <button
                                                                type="button"
                                                                onClick={() => handleActionClick(gId, b)}
                                                                disabled={isDisabled}
                                                                className={
                                                                    "px-3 py-1.5 rounded-md text-sm border hover:bg-gray-50 inline-flex items-center gap-1 " +
                                                                    (isDisabled ? "opacity-60 cursor-not-allowed" : "")
                                                                }
                                                                aria-label={b.title}
                                                            >
                                                                {b.url ? (
                                                                    <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
                                                                ) : null}
                                                                {b.title}
                                                            </button>
                                                        </IconTooltip>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </BotRow>
                            );
                        }

                        // Buttons set
                        if (m.buttons) {
                            const gId = m.id;
                            const isDisabled = disabledActionGroups.has(gId);
                            return (
                                <BotRow key={m.id} testid="msg-bot">
                                    <div
                                        className="rounded-2xl px-3 py-2 bg-gray-100 text-gray-800 max-w-[75%]"
                                        data-testid="msg-buttons"
                                    >
                                        <div className="text-xs text-gray-500 mb-2">Elige una opción:</div>
                                        <div className="flex flex-wrap gap-2">
                                            {m.buttons.map((b) => (
                                                <IconTooltip key={b.id} label={b.payload || b.title} side="top">
                                                    <button
                                                        type="button"
                                                        onClick={() => handleActionClick(gId, b)}
                                                        disabled={isDisabled}
                                                        className={
                                                            "px-3 py-1.5 rounded-md text-sm border hover:bg-gray-50 " +
                                                            (isDisabled ? "opacity-60 cursor-not-allowed" : "")
                                                        }
                                                        aria-label={b.title}
                                                    >
                                                        {b.title}
                                                    </button>
                                                </IconTooltip>
                                            ))}
                                        </div>
                                    </div>
                                </BotRow>
                            );
                        }

                        // Quick replies
                        if (m.quickReplies) {
                            const gId = m.id;
                            const isDisabled = disabledActionGroups.has(gId);
                            return (
                                <BotRow key={m.id} testid="msg-bot">
                                    <div
                                        className="rounded-2xl px-2 py-2 bg-gray-100 text-gray-800 max-w-[90%]"
                                        data-testid="msg-quick-replies"
                                    >
                                        <div className="text-xs text-gray-500 mb-2">Sugerencias:</div>
                                        <div className="flex items-center gap-2 overflow-x-auto pb-1">
                                            {m.quickReplies.map((q) => (
                                                <IconTooltip key={q.id} label={q.payload || q.title} side="top">
                                                    <button
                                                        type="button"
                                                        onClick={() => handleActionClick(gId, q)}
                                                        disabled={isDisabled}
                                                        className={
                                                            "px-3 py-1.5 rounded-full text-sm border whitespace-nowrap hover:bg-gray-50 " +
                                                            (isDisabled ? "opacity-60 cursor-not-allowed" : "")
                                                        }
                                                        aria-label={q.title}
                                                    >
                                                        {q.title}
                                                    </button>
                                                </IconTooltip>
                                            ))}
                                        </div>
                                    </div>
                                </BotRow>
                            );
                        }

                        // Text / Image
                        if (isUser) {
                            return (
                                <UserRow key={m.id} testid="msg-user">
                                    <div className={`${commonCls} ${bubbleCls}`} data-testid="msg-user-bubble">
                                        {m.text ? (
                                            <p className="whitespace-pre-wrap">{m.text}</p>
                                        ) : m.image ? (
                                            <div className="flex items-center gap-2">
                                                <ImgIcon className="w-4 h-4 opacity-70" aria-hidden="true" />
                                                <IconTooltip label="Ver imagen" side="top">
                                                    <a href={m.image} target="_blank" rel="noreferrer" className="underline">
                                                        Ver imagen
                                                    </a>
                                                </IconTooltip>
                                            </div>
                                        ) : null}
                                    </div>
                                </UserRow>
                            );
                        }
                        // bot
                        return (
                            <BotRow key={m.id} testid="msg-bot">
                                <div className={`${commonCls} ${bubbleCls}`} data-testid="msg-bot-bubble">
                                    {m.text ? (
                                        <p className="whitespace-pre-wrap">{m.text}</p>
                                    ) : m.image ? (
                                        <div className="flex items-center gap-2">
                                            <ImgIcon className="w-4 h-4 opacity-70" aria-hidden="true" />
                                            <IconTooltip label="Ver imagen" side="top">
                                                <a href={m.image} target="_blank" rel="noreferrer" className="underline">
                                                    Ver imagen
                                                </a>
                                            </IconTooltip>
                                        </div>
                                    ) : null}
                                </div>
                            </BotRow>
                        );
                    })}

                    {/* Indicador escribiendo… (bot) */}
                    {sending && (
                        <div className="flex items-start gap-2 justify-start" data-testid="chat-typing">
                            <BotAvatar />
                            <div className="rounded-2xl px-3 py-2 bg-gray-100 text-gray-600 text-sm inline-flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                                Escribiendo…
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Error inline */}
            {error ? (
                <div className="px-3" data-testid="chat-error">
                    <div className="max-w-3xl mx-auto my-2 text-xs text-red-600 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" aria-hidden="true" />
                        <span>{error}</span>
                    </div>
                </div>
            ) : null}

            {/* ✅ Composer (input + avatar + mic + enviar) con layout en línea */}
            <form
                onSubmit={onSubmitComposer}
                className={"border-t " + (embed ? "p-2" : "p-3 bg-white")}
                noValidate
            >
                <div
                    className="max-w-3xl mx-auto flex items-center gap-2"
                    data-testid="chat-composer"
                >
                    <textarea
                        className="flex-1 min-w-0 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                        placeholder={placeholder}
                        rows={2}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={onKeyDown}
                        disabled={sending}
                        aria-label="Escribe tu mensaje"
                        data-testid="chat-input"
                    />

                    {/* 👤 Avatar del usuario en la barra de entrada */}
                    <IconTooltip label={meLabel} side="top">
                        <div className="shrink-0">
                            <UserAvatar user={user} size={28} />
                        </div>
                    </IconTooltip>

                    {/* 🎤 Mic (audio) */}
                    <MicButton
                        disabled={sending}
                        onPushUser={appendUserMessage}
                        onPushBot={appendBotMessages}
                        userId={userId || undefined}
                        persona={personaFromQS || undefined}
                        lang={langFromQS || "es"}
                        className="shrink-0"
                    />

                    {/* Botón Enviar */}
                    <IconTooltip label="Enviar (Enter)">
                        <button
                            type="submit"
                            disabled={sending || !input.trim()}
                            className="shrink-0 inline-flex items-center justify-center rounded-md bg-indigo-600 text-white px-3 py-2 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            aria-label="Enviar"
                            data-testid="chat-send"
                        >
                            {sending ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                        </button>
                    </IconTooltip>
                </div>
            </form>
        </div>
    );
}