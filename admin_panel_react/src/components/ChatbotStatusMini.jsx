import React, { useState, useMemo } from "react";
import { Loader2, Bot } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import assets from "@/config/assets";

const STATUS_CONFIG = {
    ready: {
        label: "Chatbot conectado",
        ring: "ring-4 ring-emerald-400",
    },
    connecting: {
        label: "Conectando con el tutor virtual…",
        ring: "ring-4 ring-sky-400",
    },
    warning: {
        label: "Modo degradado: conexión inestable",
        ring: "ring-4 ring-amber-400",
    },
    error: {
        label: "Error de conexión con el chatbot",
        ring: "ring-4 ring-rose-400",
    },
};

const ChatbotStatusMini = React.memo(
    ({
        status = "connecting",
        message,
        avatarSrc = assets.BOT_AVATAR,
        className = "",
    }) => {
        const [imgError, setImgError] = useState(false);

        const meta = useMemo(
            () => STATUS_CONFIG[status] || STATUS_CONFIG.connecting,
            [status]
        );

        const label = message || meta.label;
        const { ring } = meta;

        return (
            <div
                className={`inline-flex items-center ${className}`}
                role="status"
                aria-live="polite"
            >
                <IconTooltip label={label} side="top">
                    {/* Contenedor del avatar, tamaño FIJO 48x48 */}
                    <div
                        className={["relative shrink-0 rounded-full", ring].join(" ")}
                        style={{ width: 48, height: 48 }} // 👈 AQUÍ fijamos el tamaño
                    >
                        {/* Avatar dentro, rellenando el círculo */}
                        <div
                            className="
                              rounded-full overflow-hidden bg-white shadow-md
                              border border-slate-900/70
                              w-full h-full flex items-center justify-center
                              transition-transform duration-150
                              hover:scale-[1.03]
                            "
                            aria-busy={status === "connecting"}
                        >
                            {imgError ? (
                                <Bot
                                    className="w-1/2 h-1/2 text-indigo-500"
                                    aria-hidden="true"
                                />
                            ) : (
                                <img
                                    src={avatarSrc}
                                    alt="Avatar del chatbot"
                                    className="object-cover w-full h-full"
                                    onError={() => setImgError(true)}
                                />
                            )}
                        </div>

                        {/* Spinner pequeño sólo en 'connecting' */}
                        {status === "connecting" && (
                            <Loader2
                                className="
                                 absolute -bottom-1 -right-1
                                 w-4 h-4
                                 animate-spin text-sky-500/80
                                 bg-white rounded-full p-0.5 shadow
                               "
                                aria-hidden="true"
                            />
                        )}
                    </div>
                </IconTooltip>
            </div>
        );
    }
);

export default ChatbotStatusMini;
