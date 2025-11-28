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
                        rounded-full overflow-hidden bg-white shadow-lg
                        border border-slate-200
                        flex items-center justify-center
                        mx-auto
                        w-24 h-24          /* móvil ≈ 96px */
                        sm:w-28 sm:h-28    /* tablet pequeña */
                        md:w-32 md:h-32    /* tablet / portátil */
                        lg:w-36 lg:h-36    /* escritorio */
                        xl:w-40 xl:h-40    /* monitores grandes */
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
                                className="object-contain w-full h-full"
                                loading="eager"
                                onError={() => setImgError(true)}
                            />
                        )}
                    </div>
                </IconTooltip>

                {useSpinner && (
                    <Loader2
                        className="
                          absolute -bottom-3 -right-3 
                          h-6 w-6 md:h-7 md:w-7 
                          animate-spin text-indigo-600 bg-white rounded-full p-0.5 shadow
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
