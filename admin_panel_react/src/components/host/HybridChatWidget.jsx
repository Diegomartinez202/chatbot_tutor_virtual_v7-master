// admin_panel_react/src/components/host/HybridChatWidget.jsx
import React, { useEffect, useRef, useState } from "react";

const ALLOWED_IFRAME_ORIGINS = [
    window.location.origin,
    "https://zajuna.sena.edu.co",
    "http://localhost:5173",
    "http://localhost:8080",
];

// 👉 que el iframe vaya a la página de inicio, no directo a /chat
//const CHAT_IFRAME_SRC = "/"; 
const CHAT_IFRAME_SRC = "/chat?embed=1&guest=1";

// 👉 ruta del avatar (archivo en public/embed/bot-avatar.png)
const AVATAR_URL = "/bot-avatar.png";

export default function HybridChatWidget({ defaultOpen = false }) {
    const [open, setOpen] = useState(!!defaultOpen);
    const [minimized, setMinimized] = useState(false);
    const frameRef = useRef(null);

    function getHostToken() {
        try {
            return (
                localStorage.getItem("host_token") ||
                localStorage.getItem("zajuna_token") ||
                null
            );
        } catch {
            return null;
        }
    }
    function postToIframe(message) {
        try {
            frameRef.current?.contentWindow?.postMessage(message, "*");
        } catch { }
    }
    function sendAuthTokenToIframe() {
        const tok = getHostToken();
        if (!tok) return;
        postToIframe({ type: "auth:token", token: tok });
    }

    useEffect(() => {
        const onMsg = (ev) => {
            const origin = ev.origin || ev.originalEvent?.origin;
            if (
                ALLOWED_IFRAME_ORIGINS.length &&
                !ALLOWED_IFRAME_ORIGINS.includes(origin)
            )
                return;
            const data = ev.data || {};
            if (!data || typeof data !== "object") return;

            if (data.type === "auth:request") {
                sendAuthTokenToIframe();
            }
            if (data.type === "widget:toggle") {
                if (data.action === "close") setOpen(false);
                else if (data.action === "open") setOpen(true);
                else setMinimized((m) => !m);
            }
        };
        window.addEventListener("message", onMsg);
        return () => window.removeEventListener("message", onMsg);
    }, []);

    function onLoad() {
        sendAuthTokenToIframe();
    }

    return (
        <>
            {!open && (
                <button
                    type="button"
                    className="chat-launcher"
                    onClick={() => setOpen(true)}
                    style={{
                        position: "fixed",
                        right: 18,
                        bottom: 18,
                        zIndex: 9998,
                        background: "#4f46e5",
                        color: "#fff",
                        border: 0,
                        borderRadius: 999,
                        padding: "8px 12px",
                        cursor: "pointer",
                        boxShadow: "0 10px 30px rgba(2,6,23,0.18)",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 8,
                    }}
                >
                    <span
                        style={{
                            width: 28,
                            height: 28,
                            borderRadius: "999px",
                            overflow: "hidden",
                            background: "#ffffff",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                        }}
                    >
                        <img
                            src={AVATAR_URL}
                            alt="Tutor Virtual"
                            style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover",
                                display: "block",
                            }}
                        />
                    </span>

                    <span style={{ fontSize: 14, fontWeight: 500 }}>Abrir chat</span>
                </button>
            )}

            {/* Bubble */}
            {open && (
                <div
                    className={`chat-bubble ${minimized ? "minimized" : ""}`}
                    style={{
                        position: "fixed",
                        right: 18,
                        bottom: 18,
                        width: 400,
                        maxWidth: "95vw",
                        height: minimized ? 52 : 580,
                        background: "#fff",
                        border: "1px solid #e2e8f0",
                        borderRadius: 16,
                        boxShadow: "0 10px 30px rgba(2,6,23,0.18)",
                        overflow: "hidden",
                        zIndex: 9999,
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    <div
                        className="chat-header"
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            padding: "8px 10px",
                            background: "#1e293b",
                            color: "#fff",
                            fontSize: 14,
                        }}
                    >
                        <strong>Tutor Virtual</strong>
                        <div style={{ display: "flex", gap: 6 }}>
                            <button
                                type="button"
                                onClick={() => setMinimized((m) => !m)}
                                className="btn"
                                style={{ padding: "4px 8px" }}
                            >
                                {minimized ? "Maximizar" : "Minimizar"}
                            </button>
                            <button
                                type="button"
                                onClick={() => setOpen(false)}
                                className="btn"
                                style={{ padding: "4px 8px" }}
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                    {!minimized && (
                        <div className="chat-body" style={{ flex: 1 }}>
                            <iframe
                                ref={frameRef}
                                className="chat-iframe"
                                title="Tutor Virtual"
                                src={CHAT_IFRAME_SRC}
                                allow="microphone; clipboard-read; clipboard-write"
                                referrerPolicy="strict-origin-when-cross-origin"
                                onLoad={onLoad}
                                style={{
                                    border: 0,
                                    width: "100%",
                                    height: "100%",
                                    display: "block",
                                }}
                            />
                        </div>
                    )}
                </div>
            )}
        </>
    );
}
