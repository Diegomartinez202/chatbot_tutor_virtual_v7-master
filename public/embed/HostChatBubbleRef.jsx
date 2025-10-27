import React, {
    forwardRef,
    useCallback,
    useEffect,
    useImperativeHandle,
    useRef,
    useState,
} from "react";

/**
 * Requiere que el host sirva los assets:
 *   /embed/zajuna-bubble.js
 *   /embed/zajuna-bubble.css
 *
 * En tu index.html (host) puedes agregar:
 *   <link rel="stylesheet" href="/embed/zajuna-bubble.css" />
 */
const HostChatBubbleRef = forwardRef(function HostChatBubbleRef(
    {
        iframeUrl = `${window.location.origin}/?embed=1`,
        allowedOrigin = window.location.origin,
        title = "Tutor Virtual",
        subtitle = "Sustentación",
        position = "bottom-right", // bottom-right | bottom-left | top-right | top-left
        startOpen = false,
        theme = "auto", // auto | light | dark
        zIndex = 999999,
        initialToken,          // token opcional al montar
        onTelemetry,           // (evt) => {}
        onAuthNeeded,          // () => {}
    },
    ref
) {
    const bubbleRef = useRef(null);
    const [mounted, setMounted] = useState(false);
    const [lastPrefs, setLastPrefs] = useState({ theme: "light", language: "es" });
    const [lastEvent, setLastEvent] = useState(null);

    // Carga el script del bubble una sola vez
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

    // Monta / desmonta el bubble
    useEffect(() => {
        let destroyed = false;

        (async () => {
            await ensureBubbleScript();
            if (destroyed) return;

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

            bubble.onEvent((evt) => {
                setLastEvent(evt);
                if (evt?.type === "telemetry") {
                    onTelemetry?.(evt); // { type:"telemetry", event:"message_sent" | "message_received" }
                } else if (evt?.type === "prefs:update") {
                    const next = {
                        theme: evt?.prefs?.theme || "light",
                        language: evt?.prefs?.language || "es",
                    };
                    setLastPrefs(next);
                    // Si theme=auto, reflejamos tema del iframe en el host
                    if (theme === "auto") {
                        document.documentElement.classList.toggle("dark", next.theme === "dark");
                    }
                } else if (evt?.type === "auth:needed") {
                    onAuthNeeded?.();
                }
            });

            bubble.mount();
            setMounted(true);
            if (startOpen) bubble.open();

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

    // Métodos públicos (expuestos vía ref)
    useImperativeHandle(
        ref,
        () => ({
            open: () => bubbleRef.current?.open?.(),
            close: () => bubbleRef.current?.close?.(),
            toggle: () => {
                const b = bubbleRef.current;
                if (!b) return;
                b.isOpen?.() ? b.close?.() : b.open?.();
            },
            sendToken: (token) => bubbleRef.current?.sendAuthToken?.(token),
            setTheme: (next) => {
                // Notifica al iframe y, si theme=auto, también al host
                bubbleRef.current?.setTheme?.(next);
                if (theme === "auto") {
                    document.documentElement.classList.toggle("dark", next === "dark");
                }
                setLastPrefs((p) => ({ ...p, theme: next || "light" }));
            },
            setLanguage: (lang) => {
                bubbleRef.current?.setLanguage?.(lang);
                setLastPrefs((p) => ({ ...p, language: lang || "es" }));
            },
            getLastEvent: () => lastEvent,
            getLastPrefs: () => lastPrefs,
        }),
        [lastEvent, lastPrefs, theme]
    );

    // Caja de estado opcional (debug). Puedes eliminar el return si no quieres UI.
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
                <div style={{ fontWeight: 600, marginBottom: 6 }}>HostChatBubbleRef (Debug)</div>
                <div style={{ fontSize: 12, opacity: 0.9 }}>
                    <div>mounted: <b>{String(mounted)}</b></div>
                    <div>lastPrefs: theme=<b>{lastPrefs.theme}</b> lang=<b>{lastPrefs.language}</b></div>
                    <div>lastEvent: <code style={{ fontSize: 11 }}>{lastEvent ? JSON.stringify(lastEvent) : "—"}</code></div>
                </div>

                <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <button onClick={() => bubbleRef.current?.open?.()} style={btn}>Abrir</button>
                    <button onClick={() => bubbleRef.current?.close?.()} style={btnSecondary}>Cerrar</button>
                    <button onClick={() => bubbleRef.current?.isOpen?.() ? bubbleRef.current?.close?.() : bubbleRef.current?.open?.()} style={btn}>
                        Toggle
                    </button>
                    <button onClick={() => bubbleRef.current?.sendAuthToken?.("FAKE_TOKEN_ZAJUNA")} style={btn}>
                        Enviar token FAKE
                    </button>
                    <button
                        onClick={() =>
                        (lastPrefs.theme === "dark"
                            ? bubbleRef.current?.setTheme?.("light")
                            : bubbleRef.current?.setTheme?.("dark"))
                        }
                        style={btn}
                    >
                        Toggle theme
                    </button>
                    <button
                        onClick={() =>
                        (lastPrefs.language === "es"
                            ? bubbleRef.current?.setLanguage?.("en")
                            : bubbleRef.current?.setLanguage?.("es"))
                        }
                        style={btnSecondary}
                    >
                        Toggle lang
                    </button>
                </div>
            </div>
        </div>
    );
});

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

export default HostChatBubbleRef;
