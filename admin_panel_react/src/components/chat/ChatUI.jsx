// src/components/chat/ChatUI.jsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Send, User as UserIcon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/context/AuthContext";
import { sendRasaMessage } from "@/services/chat/connectRasaRest";
import MicButton from "./MicButton";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { STORAGE_KEYS } from "@/lib/constants";
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";
import "./ChatUI.css";

// Evita doble saludo: aquí controlamos saludo inicial del cliente
const SEND_CLIENT_HELLO = true;

// Helpers
function getParentOrigin() {
    try {
        return new URL(document.referrer || "").origin;
    } catch {
        return window.location.origin;
    }
}
function normalize(o) {
    return String(o || "").trim().replace(/\/+$/, "");
}

const envAllowed = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "")
    .split(",")
    .map((s) => normalize(s))
    .filter(Boolean);

const BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const USER_AVATAR_FALLBACK = import.meta.env.VITE_USER_AVATAR || "/user-avatar.png";

/* --- Router local para payloads opcionales (UX instantánea) --- */
function localNodesToItems(nodes, tChat, sendToRasa) {
    return nodes
        .map((n, i) => {
            const id = `local-${Date.now()}-${i}`;
            if (n.type === "text") {
                return { id, role: "bot", text: typeof n.text === "function" ? n.text(tChat) : n.text };
            }
            if (n.type === "buttons") {
                return {
                    id,
                    role: "bot",
                    render: () => (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {n.items.map((btn, j) => (
                                <button
                                    key={j}
                                    type="button"
                                    className="bot-interactive"
                                    onClick={() =>
                                        sendToRasa({ text: btn.payload, displayAs: btn.label, isPayload: true })
                                    }
                                >
                                    {btn.label}
                                </button>
                            ))}
                        </div>
                    ),
                };
            }
            if (n.type === "links") {
                return {
                    id,
                    role: "bot",
                    render: () => (
                        <div className="flex flex-col gap-2 mt-2">
                            {n.items.map((lnk, j) => (
                                <a
                                    key={j}
                                    href={lnk.href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="bot-interactive"
                                >
                                    {lnk.label}
                                </a>
                            ))}
                        </div>
                    ),
                };
            }
            return null;
        })
        .filter(Boolean);
}

const LOCAL_ROUTES = {
    "/faq_ingreso": (tChat) => [
        { type: "text", text: () => tChat("inicio.title", "Elige una opción para continuar:") },
        {
            type: "links",
            items: [
                {
                    label: tChat("links.zajunaRegister", "Registro en Zajuna"),
                    href: "https://zajuna.example/faq/registro",
                },
                {
                    label: tChat("links.zajunaLogin", "Inicio de sesión"),
                    href: "https://zajuna.example/faq/login",
                },
                {
                    label: tChat("links.changePassword", "Cambiar contraseña"),
                    href: "https://zajuna.example/faq/password",
                },
                {
                    label: tChat("links.userBlocked", "Usuario bloqueado"),
                    href: "https://zajuna.example/faq/bloqueo",
                },
            ],
        },
        {
            type: "buttons",
            items: [
                { label: tChat("inicio.options.explorar", "Explorar temas"), payload: "/explorar_temas" },
                { label: tChat("inicio.options.cursos", "Mis cursos y contenidos"), payload: "/mis_cursos" },
                {
                    label: tChat("inicio.options.academico", "Proceso académico / administrativo"),
                    payload: "/academico_admin",
                },
                { label: tChat("inicio.options.soporte", "Soporte técnico"), payload: "/soporte_tecnico" },
            ],
        },
    ],

    "/explorar_temas": (tChat) => [
        { type: "text", text: tChat("sections.topicsFeatured", "Temas destacados:") },
        {
            type: "buttons",
            items: [
                { label: tChat("topics.pythonBasic", "Python Básico"), payload: "/tema_python_basico" },
                { label: tChat("topics.aiEducation", "IA Educativa"), payload: "/tema_ia_educativa" },
                { label: tChat("topics.excelBasic", "Excel Básico"), payload: "/tema_excel_basico" },
                { label: tChat("topics.webProgramming", "Programación Web"), payload: "/tema_programacion_web" },
            ],
        },
    ],

    "/mis_cursos": (tChat) => [
        { type: "text", text: tChat("sections.yourActiveCourses", "Tus cursos activos:") },
        {
            type: "links",
            items: [{ label: tChat("links.coursesPanel", "Mi panel de cursos"), href: "https://zajuna.example/cursos" }],
        },
    ],

    "/academico_admin": (tChat) => [
        { type: "text", text: tChat("sections.whichPart", "¿Qué parte del proceso?") },
        {
            type: "buttons",
            items: [
                { label: tChat("faq.matricula", "Matrícula"), payload: "/faq_matricula" },
                { label: tChat("faq.pagosBecas", "Pagos y becas"), payload: "/faq_pagos_becas" },
                { label: tChat("faq.certificados", "Certificados"), payload: "/faq_certificados" },
            ],
        },
    ],

    "/soporte_tecnico": (tChat) => [
        { type: "text", text: tChat("sections.supportOptions", "Opciones de soporte:") },
        {
            type: "links",
            items: [
                { label: tChat("links.usageGuide", "Guía de uso"), href: "https://zajuna.example/soporte/guia" },
                { label: tChat("links.openTicket", "Abrir ticket"), href: "https://zajuna.example/soporte/ticket" },
            ],
        },
    ],
};

async function handleLocalPayload({ text, tChat, setMessages, sendToRasa }) {
    const make = LOCAL_ROUTES[text];
    if (!make) return false;
    const nodes = make(tChat);
    const items = localNodesToItems(nodes, tChat, sendToRasa);
    if (items.length) {
        for (let i = 0; i < items.length; i++) {
            await new Promise((r) => setTimeout(r, 120));
            setMessages((m) => [...m, items[i]]);
        }
    }
    return true;
}

/* --- Avatares --- */
function BotAvatar({ size = 28 }) {
    const [err, setErr] = useState(false);
    return (
        <div
            className="shrink-0 rounded-full overflow-hidden border border-gray-200 bg-white flex items-center justify-center"
            style={{ width: size, height: size }}
        >
            {err ? (
                <UserIcon className="w-4 h-4 text-indigo-600" />
            ) : (
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
            <div
                className="shrink-0 rounded-full border border-gray-200 bg-gray-100 text-gray-700 flex items-center justify-center font-semibold"
                style={{ width: size, height: size }}
            >
                {initials?.slice(0, 2) || <UserIcon className="w-4 h-4" />}
            </div>
        );
    }
    return (
        <img
            src={src}
            alt={user?.nombre || user?.name || user?.email}
            className="w-full h-full object-cover rounded-full"
            onError={() => setErr(true)}
        />
    );
}

export default function ChatUI({ embed = false, placeholder = "Escribe un mensaje…" }) {
    const { user } = useAuth();
    const { t: tChat } = useTranslation("chat");
    const { t: tConfig } = useTranslation("config");

    const storeToken = useAuthStore((s) => s.accessToken);
    const [authToken, setAuthToken] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [typing, setTyping] = useState(false);

    // Sugerencias: switches
    const [hasShownSuggestions, setHasShownSuggestions] = useState(false);
    const [hasSentFirstMessage, setHasSentFirstMessage] = useState(false);

    // Saludo inicial inmediato
    useEffect(() => {
        if (SEND_CLIENT_HELLO) {
            setMessages([
                {
                    id: "welcome",
                    role: "bot",
                    text: tChat("welcome", "¡Hola! Soy tu tutor virtual 🤖. ¿En qué puedo ayudarte hoy?"),
                },
            ]);
        }
    }, [tChat]);

    // Token centralizado / localStorage
    useEffect(() => {
        if (storeToken) setAuthToken(storeToken);
        else {
            try {
                const ls =
                    localStorage.getItem(STORAGE_KEYS.accessToken) || localStorage.getItem("zajuna_token");
                if (ls) setAuthToken(ls);
            } catch { }
        }
    }, [storeToken]);

    const userId = useMemo(() => user?.email || user?._id || null, [user]);
    const parentOrigin = useMemo(() => normalize(getParentOrigin()), []);

    // Detecta modo invitado en embed: /?embed=1&guest=1
    const urlParams = new URLSearchParams(window.location.search);
    const isGuestEmbed = urlParams.get("guest") === "1";

    // ANTES: const needAuth = embed || !user;
    // AHORA: en modo invitado NO pedimos login
    const needAuth = !isGuestEmbed && (embed || !user);

    // Embed: recibe token del host
    useEffect(() => {
        if (!embed) return;
        const onMsg = (ev) => {
            try {
                const origin = normalize(ev.origin || "");
                if (envAllowed.length && !envAllowed.includes(origin)) return;
                const data = ev.data || {};
                if (data?.type === "auth:token" && data?.token) setAuthToken(String(data.token));
            } catch { }
        };
        window.addEventListener("message", onMsg);
        return () => window.removeEventListener("message", onMsg);
    }, [embed]);

    const rspToArray = (rsp) => (Array.isArray(rsp) ? rsp : rsp ? [rsp] : []);

    const appendBotMessages = useCallback(
        async (rsp) => {
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
                                    <button
                                        key={i}
                                        type="button"
                                        className="bot-interactive"
                                        onClick={() => handleActionClick(baseId, btn)}
                                    >
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
                                    <button
                                        key={i}
                                        type="button"
                                        className="bot-interactive"
                                        onClick={() => handleActionClick(baseId, qr)}
                                    >
                                        {qr.title}
                                    </button>
                                ))}
                            </div>
                        ),
                    });
                }
            });
            if (!items.length)
                items.push({ id: `b-${Date.now()}-empty`, role: "bot", text: tChat("noResponse") });

            setTyping(true);
            for (let i = 0; i < items.length; i++) {
                await new Promise((r) => setTimeout(r, 140));
                setMessages((m) => [...m, items[i]]);
            }
            setTyping(false);

            try {
                window.parent?.postMessage({ type: "telemetry", event: "message_received" }, "*");
            } catch { }
        },
        [tChat]
    );

    // Sugerencias iniciales (si decides usarlas además del primer payload local)
    const appendFirstSuggestions = useCallback(() => {
        if (hasShownSuggestions) return;
        const opts = [
            { label: tChat("inicio.options.explorar", "Explorar temas"), payload: "/explorar_temas" },
            { label: tChat("inicio.options.ingreso", "Ingreso a Zajuna"), payload: "/faq_ingreso" },
            { label: tChat("inicio.options.cursos", "Mis cursos y contenidos"), payload: "/mis_cursos" },
            {
                label: tChat("inicio.options.academico", "Proceso académico / administrativo"),
                payload: "/academico_admin",
            },
            { label: tChat("inicio.options.soporte", "Soporte técnico"), payload: "/soporte_tecnico" },
        ];
        setMessages((m) => [
            ...m,
            {
                id: `b-${Date.now()}-intro`,
                role: "bot",
                text: tChat("inicio.title", "Puedo ayudarte en estos temas:"),
            },
            {
                id: `b-${Date.now()}-opts`,
                role: "bot",
                render: () => (
                    <div className="flex flex-wrap gap-2 mt-2">
                        {opts.map((btn, i) => (
                            <button
                                key={i}
                                type="button"
                                className="bot-interactive"
                                onClick={() => sendToRasa({ text: btn.payload, displayAs: btn.label, isPayload: true })}
                            >
                                {btn.label}
                            </button>
                        ))}
                    </div>
                ),
            },
        ]);
        setHasShownSuggestions(true);
    }, [hasShownSuggestions, tChat]);

    /* --- sendToRasa con handler local --- */
    const sendToRasa = async ({ text, displayAs, isPayload = false }) => {
        setError("");

        // Si el embed está en modo invitado, NUNCA pedimos login
        if (needAuth && !authToken) {
            window.parent?.postMessage?.({ type: "auth:needed" }, "*");
            setError(tChat("authRequired"));
            return;
        }

        // pinta el mensaje del usuario
        setSending(true);
        setMessages((m) => [...m, { id: `u-${Date.now()}`, role: "user", text: displayAs || text }]);
        setInput("");

        // Al primer mensaje del usuario, empuja menú local de forma inmediata
        if (!hasSentFirstMessage) {
            setHasSentFirstMessage(true);
            await handleLocalPayload({
                text: "/explorar_temas",
                tChat,
                setMessages,
                sendToRasa,
            });
            // Evita que luego se dupliquen con appendFirstSuggestions
            setHasShownSuggestions(true);
        }

        // (Opcional) si mantienes las sugerencias clásicas también:
        if (!isPayload && !hasShownSuggestions && hasSentFirstMessage) {
            appendFirstSuggestions();
        }

        try {
            window.parent?.postMessage?.({ type: "telemetry", event: "message_sent" }, "*");
        } catch { }

        try {
            // si es payload, además de la respuesta local, consulta a Rasa
            if (isPayload) {
                await handleLocalPayload({ text, tChat, setMessages, sendToRasa });
            }

            const rsp = await sendRasaMessage({
                text,
                sender: userId || undefined,
                token: authToken || undefined,
            });
            await appendBotMessages(rsp);
        } catch (e) {
            setError(e?.message || tChat("errorSending"));
        } finally {
            setSending(false);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || sending) return;
        await sendToRasa({ text: input });
    };
    try {
        window.parent?.postMessage({ type: "widget:open" }, "*");
    } catch { /* no-op */ }
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

    const BotRow = ({ children }) => (
        <div className="flex items-start gap-2 justify-start animate-fade-slide">{children}</div>
    );
    const UserRow = ({ children }) => (
        <div className="flex items-start gap-2 justify-end animate-fade-slide">{children}</div>
    );

    return (
        <div className="h-full flex flex-col chat-container">
            {/* Header simple con Config a la derecha */}
            <div className="chat-header">
                <div className="chat-title">Asistente</div>
                <div className="ml-auto">
                    <ChatConfigMenu />
                </div>
            </div>

            <div className="chat-messages px-3 py-4">
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
                            {tChat("typing")}
                            <span className="typing-dots" />
                        </div>
                    </BotRow>
                )}
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="chat-input-container">
                <MicButton onVoice={(p) => sendToRasa({ text: p })} disabled={sending} />
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

