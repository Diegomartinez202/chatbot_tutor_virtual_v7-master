// src/components/ChatbotStatusMini.jsx
import React, { useState, useMemo } from "react";
import { Loader2, Bot, CheckCircle, XCircle } from "lucide-react";
import Badge from "@/components/Badge";
import IconTooltip from "@/components/ui/IconTooltip";
import assets from "@/config/assets";

const STATUS_MAP = {
    connecting: { badge: "pendiente", label: "Conectando…" },
    ready: { badge: "ok", label: "Conectado" },
    error: { badge: "error", label: "Error de conexión" },
};

const ChatbotStatusMini = React.memo(
    ({ status = "connecting", message, avatarSrc = assets.BOT_AVATAR, sizeClass = "w-9 h-9", className = "" }) => {
        const [imgError, setImgError] = useState(false);
        const meta = useMemo(() => STATUS_MAP[status] || STATUS_MAP.connecting, [status]);
        const label = message || meta.label;

        const statusIcon = useMemo(() => {
            if (status === "connecting")
                return <Loader2 className="absolute -bottom-1 -right-1 h-4 w-4 animate-spin text-indigo-600 bg-white rounded-full p-0.5" aria-hidden="true" />;
            if (status === "ready")
                return <CheckCircle className="absolute -bottom-1 -right-1 h-4 w-4 text-green-600 bg-white rounded-full" aria-hidden="true" />;
            if (status === "error")
                return <XCircle className="absolute -bottom-1 -right-1 h-4 w-4 text-red-600 bg-white rounded-full" aria-hidden="true" />;
            return null;
        }, [status]);

        return (
            <div className={`inline-flex items-center gap-2 ${className}`} role="status" aria-live="polite">
                <div className="relative">
                    <IconTooltip label={label} side="top">
                        <div className={`rounded-full overflow-hidden bg-white shadow border border-gray-200 flex items-center justify-center ${sizeClass}`} aria-busy={status === "connecting"}>
                            {imgError ? <Bot className="w-5 h-5 text-indigo-600" aria-hidden="true" /> : <img src={avatarSrc} alt="Avatar del chatbot" className="object-cover w-full h-full" onError={() => setImgError(true)} />}
                        </div>
                    </IconTooltip>
                    {statusIcon}
                </div>

                <div className="flex flex-col">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
                    <Badge type="status" value={meta.badge} size="xs" />
                </div>
            </div>
        );
    }
);

export default ChatbotStatusMini;