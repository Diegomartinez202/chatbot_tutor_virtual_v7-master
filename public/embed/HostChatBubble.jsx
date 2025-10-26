import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";

/**
 * Requiere que el host sirva los assets:
 *   /embed/zajuna-bubble.js
 *   /embed/zajuna-bubble.css
 *
 * En Vite puedes referenciar CSS estático desde public:
 *   <link rel="stylesheet" href="/embed/zajuna-bubble.css" />
 * o importarlo si usas un empaquetado de estilos global:
 *   import "/embed/zajuna-bubble.css";
 */
export default function HostChatBubble({
    iframeUrl = `${window.location.origin}/?embed=1`,
    allowedOrigin = window.location.origin,
    title = "Tutor Virtual",
    subtitle = "Sustentación",
    position = "bottom-right", // bottom-right | bottom-left | top-right | top-left
    startOpen = false,
    theme = "auto", // auto | light | dark
    zIndex = 999999,
    // token inicial opcional (si ya estás autenticado en el host)
    initialToken,
    // callback para ver/guardar telemetría en tu app
    onTelemetry,
    // callback cuando el iframe pide auth (auth:needed)
    onAuthNeeded,
}) {
    const bubbleRef = useRef(null);
    const [mounted, setMounted] = useState(false);
    const [lastPrefs, setLastPrefs] = useState({ theme: "light", language: "es" });
    const [lastEvent, setLastEvent] = useState(null);

    // Helper para cargar el script sólo una vez
    const ensureBubbleScript = useCallback(() => {
        return new Promise((resolve, reject) => {
            if (window.ZajunaBubble) return resolve(true);
            const s = document.createElement("script");
            s.src = "/embed/zajuna-bubble.js";
            s.async = true;
            s.onload = () => resolve(true);
            s.onerror = (e) => reject(e);
            document.head.appendChild(s);
        });
    }, []);

    // Monta/desmonta
    useEffect(() => {
        let destroyed = false;

        (async () => {
            await ensureBubbleScript();
            if (destroyed) return;

            // crea instancia
            const bubble = window.ZajunaBubble.create({
                iframeUrl,
                allowedOrigin,
                title,
                subtitle,
                position,
                startOpen,
                theme,
                zIndex,
            });

            // escucha eventos del iframe
            bubble.onEvent((evt) => {
                setLastEvent(evt);
                if (evt?.type === "telemetry") {
                    onTelemetry?.(evt); // {type:"telemetry", event:"message_sent"|...}
                } else if (evt?.type === "prefs:update") {
                    const next = {
                        theme: evt?.prefs?.theme || "light",
                        language: evt?.prefs?.language || "es",
                    };
                    setLastPrefs(next);
                    // ejemplo: sincronizar tema del host
                    if (theme === "auto") {
                        document.documentElement.classList.toggle("dark", next.theme === "dark");
                    }
                } else if (evt?.type === "auth:needed") {
                    onAuthNeeded?.(); // tu app puede abrir login o recuperar token
                }
            });

            // Monta y abre
            bubble.mount();
            setMounted(true);
            bubble.open();

            // Envía token inicial si existe
            if (initialToken) {
                bubble.sendAuthToken(initialToken);
            }

            bubbleRef.current = bubble;
        })();

        return () => {
            destroyed = true;
            try {
                bubbleRef.current?.unmount?.();
            } catch { }
            bubbleRef.current = null;
            setMounted(false);
        };
    }, [
        ensureBubbleScript,
        iframeUrl,
        allowedOrigin,
        title,
        subtitle,
        position,
        startOpen,
        theme,
        zIndex,
        initialToken,
        onTelemetry,
        onAuthNeeded,
    ]);

    // API sencillo hacia el padre (host)
    const sendToken = useCallback((token) => {
        bubbleRef.current?.sendAuthToken?.(token);
    }, []);

    const setTheme = useCallback((next) => {
        bubbleRef.current?.setTheme?.(next); // notifica al iframe (si lo escuchas)
        if (theme === "auto") {
            // si el host quiere reflejarlo también:
            document.documentElement.classList.toggle("dark", next === "dark");
        }
    }, [theme]);

    const setLanguage = useCallback((lang) => {
        bubbleRef.current?.setLanguage?.(lang);
    }, []);

    // UI mínima (debug info + controles de ejemplo)
    return (
        <div style={{ position: "fixed", left: 8, bottom: 8, padding: 8, zIndex: zIndex + 1 }}>
            <div
                style={{
                    background: "rgba(15, 23, 42, .6)",
                    backdropFilter: "saturate(1.2) blur(4px)",
                    color: "#e5e7eb",
                    border: "1px solid #334155",
                    borderRadius: 12,
                    padding: 10,
                    minWidth: 260,
                }}
            >
                <div style={{ fontWeight: 600, marginBottom: 6 }}>HostChatBubble (Debug)</div>
                <div style={{ fontSize: 12, opacity: 0.9 }}>
                    <div>mounted: <b>{String(mounted)}</b></div>
                    <div>lastPrefs: theme=<b>{lastPrefs.theme}</b> lang=<b>{lastPrefs.language}</b></div>
                    <div>lastEvent: <code style={{ fontSize: 11 }}>{lastEvent ? JSON.stringify(lastEvent) : "—"}</code></div>
                </div>

                <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <button
                        onClick={() => bubbleRef.current?.open?.()}
                        className="btn"
                        style={btn}
                    >Abrir</button>
                    <button
                        onClick={() => bubbleRef.current?.close?.()}
                        className="btn"
                        style={btnSecondary}
                    >Cerrar</button>
                    <button
                        onClick={() => sendToken("FAKE_TOKEN_ZAJUNA")}
                        className="btn"
                        style={btn}
                    >Enviar token FAKE</button>
                    <button
                        onClick={() => setTheme(lastPrefs.theme === "dark" ? "light" : "dark")}
                        className="btn"
                        style={btn}
                    >Toggle theme</button>
                    <button
                        onClick={() => setLanguage(lastPrefs.language === "es" ? "en" : "es")}
                        className="btn"
                        style={btnSecondary}
                    >Toggle lang</button>
                </div>
            </div>
        </div>
    );
}

// estilos inline simples
const btn = {
    cursor: "pointer",
    background: "#4f46e5",
    color: "white",
    border: 0,
    borderRadius: 10,
    padding: "6px 10px",
    fontSize: 12,
};

const btnSecondary = {
    ...btn,
    background: "#1f2937",
    border: "1px solid #374151",
};
