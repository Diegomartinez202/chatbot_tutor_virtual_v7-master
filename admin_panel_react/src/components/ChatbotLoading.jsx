// src/components/ChatbotLoading.jsx
import React, { useState } from "react";
import { Loader2, Bot } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";
import assets from "@/config/assets";
import { useAvatarPreload } from "@/hooks/useAvatar";

export default function ChatbotLoading({
    avatarSrc = assets.BOT_LOADING,
    label = "Cargando…",
    useSpinner = true,
    showStatusBadge = false,
    status,
    statusMessage,
}) {
    const [imgError, setImgError] = useState(false);
    const statusMap = { connecting: "pendiente", ready: "ok", error: "error" };
    const statusValue = statusMap[status || ""] || status;

    useAvatarPreload(avatarSrc || assets.BOT_AVATAR);

    return (
        <div className="w-full h-full flex flex-col items-center justify-center gap-3" role="status" aria-live="polite">
            <div className="relative">
                <IconTooltip label={label} side="top">
                    <div className="w-20 h-20 rounded-full shadow-lg overflow-hidden bg-white flex items-center justify-center" aria-busy={useSpinner}>
                        {imgError ? (
                            <div className="w-full h-full flex items-center justify-center bg-indigo-600 text-white">
                                <Bot className="w-8 h-8" aria-hidden="true" />
                            </div>
                        ) : (
                            <img
                                src={avatarSrc}
                                alt="Avatar del chatbot"
                                className="w-full h-full object-cover"
                                loading="eager"
                                onError={() => setImgError(true)}
                            />
                        )}
                    </div>
                </IconTooltip>

                {useSpinner && (
                    <Loader2 className="absolute -bottom-1 -right-1 h-5 w-5 animate-spin text-indigo-600 bg-white rounded-full p-0.5" aria-hidden="true" />
                )}
            </div>

            <div className="flex flex-col items-center gap-1">
                <p className="text-sm text-gray-600 dark:text-gray-300">{label}</p>
                {showStatusBadge && statusValue && (
                    <Badge type="status" value={statusValue} size="xs">
                        {statusMessage || statusValue}
                    </Badge>
                )}
            </div>
        </div>
    );
}