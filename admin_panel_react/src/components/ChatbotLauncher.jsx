import React, { useState } from "react";
import { Bot } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import assets from "@/config/assets";
import assets from "@/config/assets";
import { useAvatarPreload } from "@/hooks/useAvatar";
/**
 * Botón flotante para abrir/cerrar el chat.
 */
export default function ChatbotLauncher({
    onClick,
    avatarSrc = assets.BOT_AVATAR,
    size = 64,
    ariaLabel = "Abrir chat",
    title = "Abrir chat",
    isOpen = false,
}) {
    const [imgError, setImgError] = useState(false);
useAvatarPreload(avatarSrc || assets.BOT_AVATAR);
    return (
        <IconTooltip label={title} side="left">
            <button
                onClick={onClick}
                className="fixed bottom-6 right-6 z-50 rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
                style={{ width: size, height: size }}
                aria-label={ariaLabel}
                aria-pressed={isOpen}
                aria-expanded={isOpen}
                title={title}
                type="button"
            >
                {imgError ? (
                    <div
                        className="w-full h-full rounded-full flex items-center justify-center bg-indigo-600 text-white"
                        style={{ width: size, height: size }}
                    >
                        <Bot className="w-1/2 h-1/2" aria-hidden="true" />
                    </div>
                ) : (
                    <img
                        src={avatarSrc}
                        alt="Chatbot"
                        className="rounded-full object-cover"
                        style={{ width: size, height: size }}
                        loading="lazy"
                        onError={() => setImgError(true)}
                    />
                )}
            </button>
        </IconTooltip>
    );
}