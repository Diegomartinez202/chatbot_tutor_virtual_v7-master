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
        <div
            className="
                w-full h-full flex flex-col items-center justify-center gap-4 
                px-4 py-6
            "
            role="status"
            aria-live="polite"
        >
            {/* Avatar responsivo */}
            <div className="relative flex items-center justify-center">
                <IconTooltip label={label} side="top">
                    <div
                        className="
                            rounded-full shadow-md overflow-hidden bg-white flex items-center justify-center
                            w-20 h-20 
                            sm:w-24 sm:h-24 
                            md:w-28 md:h-28
                        "
                        aria-busy={useSpinner}
                    >
                        {imgError ? (
                            <div className="w-full h-full flex items-center justify-center bg-indigo-600 text-white">
                                <Bot className="w-10 h-10" aria-hidden="true" />
                            </div>
                        ) : (
                            <img
                                src={avatarSrc}
                                alt="Avatar del chatbot"
                                className="
                                    object-contain 
                                    w-full h-full 
                                    p-1
                                "
                                loading="eager"
                                onError={() => setImgError(true)}
                            />
                        )}
                    </div>
                </IconTooltip>

                {useSpinner && (
                    <Loader2
                        className="
                            absolute -bottom-2 -right-2 
                            h-5 w-5 md:h-6 md:w-6 
                            animate-spin text-indigo-600 bg-white rounded-full p-0.5
                        "
                        aria-hidden="true"
                    />
                )}
            </div>

            {/* Texto + badge */}
            <div className="flex flex-col items-center gap-1">
                <p className="text-sm text-gray-700">{label}</p>

                {showStatusBadge && statusValue && (
                    <Badge type="status" value={statusValue} size="xs">
                        {statusMessage || statusValue}
                    </Badge>
                )}
            </div>
        </div>
    );
}
