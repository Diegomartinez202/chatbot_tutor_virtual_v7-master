// src/pages/ChatPage.jsx
import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Bot, RefreshCw } from "lucide-react";
import ChatUI from "@/components/chat/ChatUI";

import ChatbotLoading from "@/components/ChatbotLoading";
import ChatbotStatusMini from "@/components/ChatbotStatusMini";
import { useAuth } from "@/context/AuthContext";

// Health universal (REST/WS) — no envía mensajes al bot, solo comprueba disponibilidad
import { connectChatHealth } from "@/services/chat/health";
// Conexión WS opcional (si lo quieres usar como connectFn)
import { connectWS } from "@/services/chat/connectWS";

// Harness QA (solo se muestra si el flag lo permite)
import Harness from "@/pages/Harness";

// ⚙️ Menú de configuración (accesibilidad: idioma/tema, salir, accesos admin/SSO, etc.)
import ChatConfigMenu from "@/components/chat/ChatConfigMenu";

/**
 * Página completa del chat.
 * - Ruta /chat (con o sin login según VITE_CHAT_REQUIRE_AUTH) y modo embed (?embed=1)
 * - Estados: connecting | ready | error
 * - Si se pasa children, renderiza tu UI; si no, <ChatUI />
 * - Prop opcional `embedHeight` para controlar la altura en modo embed
 */

// ---- Config de endpoints con fallbacks sólidos al proxy de Nginx ----
const API_BASE =
    import.meta.env.VITE_API_BASE /* genérico */ ||
    "/api";

const CHAT_REST_URL =
    import.meta.env.VITE_CHAT_REST_URL /* el que ya usas */ ||
    `${API_BASE.replace(/\/$/, "")}/chat`;

const RASA_HTTP_URL =
    import.meta.env.VITE_RASA_REST_URL /* el que ya usas */ ||
    import.meta.env.VITE_RASA_HTTP /* genérico */ ||
    "/rasa";

const RASA_WS_URL =
    import.meta.env.VITE_RASA_WS_URL /* el que ya usas */ ||
    import.meta.env.VITE_RASA_WS /* genérico */ ||
    "/ws";

const DEFAULT_BOT_AVATAR = import.meta.env.VITE_BOT_AVATAR || "/bot-avatar.png";
const SHOW_HARNESS = import.meta.env.VITE_SHOW_CHAT_HARNESS === "true";
const CHAT_REQUIRE_AUTH = import.meta.env.VITE_CHAT_REQUIRE_AUTH === "true";
const TRANSPORT = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();

export default function ChatPage({
    forceEmbed = false,
    avatarSrc = DEFAULT_BOT_AVATAR,
    title = "Asistente",
    // Tip: puedes pasar un connectFn propio desde arriba si quieres forzar uno
    connectFn,
    embedHeight = "560px",
    children,
}) {
    const [params] = useSearchParams();
    const isEmbed = forceEmbed || params.get("embed") === "1";

    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    const [status, setStatus] = useState("connecting"); // connecting | ready | error

    // Elegimos la función de conexión por defecto:
    // - Si prop connectFn viene, se respeta.
    // - Si TRANSPORT=ws, validamos socket; si no, health universal (REST/WS).
    const defaultConnect = useMemo(() => {
        if (connectFn) return connectFn;

        if (TRANSPORT === "ws") {
            // Validar que el socket abre/cierra (no manda mensajes)
            return () => connectWS({ wsUrl: RASA_WS_URL });
        }
        // Por defecto: health REST/WS universal (no golpea /api/chat)
        return () =>
            connectChatHealth({
                restUrl: CHAT_REST_URL,
                rasaHttpUrl: RASA_HTTP_URL,
            });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [connectFn, TRANSPORT]);

    const connect = useCallback(async () => {
        setStatus("connecting");
        try {
            // Log suave para ayudar a depurar 404/URLs en desarrollo
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
                await defaultConnect(); // ← usa health / handshake, no /api/chat
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

    useEffect(() => {
        connect();
    }, [connect]);

    // 🔒 Control de acceso:
    // - Si ES embed → nunca exigimos login
    // - Si NO es embed → exigimos login SOLO si VITE_CHAT_REQUIRE_AUTH === "true"
    useEffect(() => {
        if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) {
            navigate("/login", { replace: true });
        }
    }, [isEmbed, isAuthenticated, navigate]);

    if (!isEmbed && CHAT_REQUIRE_AUTH && !isAuthenticated) return null;

    // Si el flag del Harness está activo y NO es embed → muestra la página de QA
    if (SHOW_HARNESS && !isEmbed) {
        return <Harness />;
    }

    // Estilos/estructura del contenedor según modo
    const wrapperClass = isEmbed ? "p-0" : "p-6 min-h-[70vh] flex flex-col";
    const bodyClass = isEmbed
        ? "h-full"
        : "flex-1 bg-white rounded border shadow overflow-hidden";
    const wrapperStyle = isEmbed ? { height: embedHeight } : undefined;

    return (
        <div className={wrapperClass} style={wrapperStyle}>
            {/* Header (oculto en embed) */}
            {!isEmbed && (
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-indigo-600" />
                        <h1 className="text-2xl font-bold">{title}</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <ChatbotStatusMini status={status} />
                        {/* ⚙️ Menú de configuración */}
                        <ChatConfigMenu />
                    </div>
                </div>
            )}

            {/* Body */}
            <div className={bodyClass} data-testid="chat-root">
                {status === "connecting" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6">
                        <ChatbotLoading avatarSrc={avatarSrc} label="Conectando…" />
                        <ChatbotStatusMini status="connecting" />
                    </div>
                )}

                {status === "error" && (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6 text-center">
                        <p className="text-gray-700">No pudimos conectar con el servicio de chat.</p>
                        <button
                            onClick={connect}
                            className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-100"
                            type="button"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Reintentar
                        </button>
                    </div>
                )}

                {status === "ready" && (
                    <div className="w-full h-full">
                        {/* Tu widget real; si no pasas children, usa ChatUI */}
                        {children ?? <ChatUI embed={isEmbed} />}
                    </div>
                )}
            </div>
        </div>
    );
}

/* Ejemplos de uso:
   - REST (default health check):
     <ChatPage />

   - Forzar WebSocket:
     <ChatPage connectFn={() => connectWS({ wsUrl: import.meta.env.VITE_RASA_WS_URL })} />

   - Forzar modo embed con altura custom:
     <ChatPage forceEmbed embedHeight="100vh" />
*/