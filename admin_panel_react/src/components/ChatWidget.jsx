//\src\components\ChatWidget.jsx
import React, { useEffect, useState, useCallback } from "react";
import { X, Bot, RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";
import ChatbotLauncher from "@/components/ChatbotLauncher";
import ChatbotLoading from "@/components/ChatbotLoading";
import ChatbotStatusMini from "@/components/ChatbotStatusMini";
import IconTooltip from "@/components/ui/IconTooltip";
import ChatUI from "@/components/chat/ChatUI";
import assets from "@/config/assets";
import { useAvatarPreload } from "@/hooks/useAvatar";
import useRasaStatus from "@/hooks/useRasaStatus";
export default function ChatWidget({
    connectFn,
    title = "Asistente",
    avatarSrc = assets.BOT_AVATAR,
    launcherSize = 64,
    defaultOpen = false,
    children,
}) {
    const { t } = useTranslation();
    const [open, setOpen] = useState(defaultOpen);
    const { status, checkStatus } = useRasaStatus();

    const connect = useCallback(async () => {
        await checkStatus();
    }, [checkStatus]);

  
    useEffect(() => {
        if (open) connect();
    }, [open, connect]);

    useEffect(() => {
        if (!open) return;
        const onEsc = (e) => e.key === "Escape" && setOpen(false);
        document.addEventListener("keydown", onEsc);
        return () => document.removeEventListener("keydown", onEsc);
    }, [open]);

    useAvatarPreload(avatarSrc || assets.BOT_AVATAR);

    return (
        <>
            <ChatbotLauncher
                onClick={() => setOpen((o) => !o)}
                avatarSrc={avatarSrc}
                size={launcherSize}
                ariaLabel={open ? t("close_chat") : t("open_chat")}
                title={open ? t("close_chat") : t("open_chat")}
                isOpen={open}
            />

            {open && (
                <div
                    className="fixed inset-0 z-[60] bg-black/40"
                    aria-modal="true"
                    role="dialog"
                    onMouseDown={(e) => e.target === e.currentTarget && setOpen(false)}
                >
                    <div
                        className="absolute right-6 bottom-6 w-[min(420px,95vw)] h-[min(70vh,640px)] bg-white rounded-2xl border shadow-2xl flex flex-col overflow-hidden"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Bot className="w-5 h-5 text-indigo-600" />
                                <h2 className="font-semibold">{t("assistant_title", { defaultValue: title })}</h2>
                            </div>
                            <div className="flex items-center gap-2">
                                <ChatbotStatusMini status={status} />
                                <IconTooltip label={t("close")} side="left">
                                    <button
                                        onClick={() => setOpen(false)}
                                        aria-label={t("close_chat")}
                                        className="p-2 rounded hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300"
                                        type="button"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </IconTooltip>
                            </div>
                        </div>

                        {/* Body */}
                        <div className="flex-1">
                            {status === "connecting" && (
                                <ChatbotLoading avatarSrc={avatarSrc} label={t("connecting")} useSpinner />
                            )}

                            {status === "error" && (
                                <div className="w-full h-full flex flex-col items-center justify-center gap-3 p-6 text-center">
                                    <p className="text-gray-700">{t("chat_connection_error")}</p>
                                    <button
                                        onClick={connect}
                                        className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-100"
                                        type="button"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        {t("retry")}
                                    </button>
                                </div>
                            )}

                            {status === "ready" && (
                                <div className="w-full h-full">
                                    {children ?? <ChatUI embed avatarSrc={avatarSrc} />}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}