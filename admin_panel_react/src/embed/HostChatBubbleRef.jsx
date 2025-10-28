// admin_panel_react/src/embed/HostChatBubbleRef.jsx
import React, {
    forwardRef,
    useCallback,
    useEffect,
    useImperativeHandle,
    useRef,
    useState,
} from "react";
avatar = { import.meta.env.VITE_BOT_AVATAR || "/mi-avatar.png" }

/** Tipados de eventos (comentarios JSDoc) omitidos por brevedad; se mantiene el contrato. */

// IDs únicos para evitar cargas duplicadas
const JS_ID = "zajuna-bubble-js";
const CSS_ID = "zajuna-bubble-css";

/** Carga segura del JS del bubble (de-dupe + timeout) */
function loadBubbleScript(src = "/embed/zajuna-bubble.js", timeoutMs = 15000) {
    return new Promise((resolve, reject) => {
        if (window.ZajunaBubble?.create) return resolve(true);

        const existing = document.getElementById(JS_ID);
        if (existing) {
            const done = () => resolve(true);
            existing.addEventListener("load", done, { once: true });
            existing.addEventListener("error", reject, { once: true });
            setTimeout(
                () =>
                    window.ZajunaBubble?.create
                        ? resolve(true)
                        : reject(new Error("[zajuna-bubble] load timeout (existing)")),
                timeoutMs
            );
            return;
        }
        const s = document.createElement("script");
        s.id = JS_ID;
        s.src = src;
        s.async = true;
        s.onload = () => resolve(true);
        s.onerror = (e) => reject(e);
        document.head.appendChild(s);
        setTimeout(
            () =>
                window.ZajunaBubble?.create
                    ? resolve(true)
                    : reject(new Error("[zajuna-bubble] load timeout")),
            timeoutMs
        );
    });
}

/** Inyecta CSS si falta */
function ensureBubbleCss(href = "/embed/zajuna-bubble.css") {
    if (document.getElementById(CSS_ID)) return;
    const already = [...document.querySelectorAll('link[rel="stylesheet"]')].some((l) =>
        (l.getAttribute("href") || "").includes(href)
    );
    if (already) return;
    const link = document.createElement("link");
    link.id = CSS_ID;
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
}

/**
 * NOTA IMPORTANTE (para /public/embed/zajuna-bubble.js):
 * Asegúrate de configurar el iframe con:
 *   iframe.allow = "microphone; camera; autoplay; clipboard-write; fullscreen";
 *   iframe.setAttribute("sandbox", "allow-same-origin allow-scripts allow-forms allow-popups");
 * para evitar los warnings de Feature Policy y permitir micro/cámara si los usas.
 */

const HostChatBubbleRef = forwardRef(function HostChatBubbleRef(
    {
        iframeUrl = `${window.location.origin}/?embed=1`,
        allowedOrigin = window.location.origin,
        title = "Tutor Virtual",
        subtitle = "Sustentación",
        position = "bottom-right",
        startOpen = false, // ⬅️ por defecto cerrado; el host decide abrirlo
        theme = "auto",
        zIndex = 2147483000,
        initialToken,
        onTelemetry,
        onAuthNeeded = () => {
            // no forzamos login automáticamente: el host decide
            console.warn("[bubble] auth:needed (ignorado por defecto; modo invitado posible)");
        },
        injectCss = true,
        showDebug = false,
        // avatar visible en el FAB del widget (pasado al bubble js)
        avatar = "/embed/mi-avatar.png",
    },
    ref
) {
    const bubbleRef = useRef(null);
    const [mounted, setMounted] = useState(false);
    const [lastPrefs, setLastPrefs] = useState({ theme: "light", language: "es" });
    const [lastEvent, setLastEvent] = useState(null);
    const [error, setError] = useState("");

    const ensureBubble = useCallback(async () => {
        if (injectCss) ensureBubbleCss("/embed/zajuna-bubble.css");
        await loadBubbleScript("/embed/zajuna-bubble.js");
        if (!window.ZajunaBubble?.create) {
            throw new Error("[HostChatBubbleRef] window.ZajunaBubble.create no disponible");
        }
    }, [injectCss]);

    useEffect(() => {
        let destroyed = false;

        (async () => {
            try {
                await ensureBubble();
            } catch (e) {
                console.warn(e);
                if (!destroyed) setError(String(e?.message || e));
                // reintento corto único
                try {
                    await new Promise((r) => setTimeout(r, 400));
                    await ensureBubble();
                } catch (e2) {
                    if (!destroyed) setError(String(e2?.message || e2));
                    return;
                }
            }
            if (destroyed) return;

            // Pista de allowedOrigin (omite warning si allowedOrigin="*")
            const expectedOrigin = new URL(iframeUrl, window.location.href).origin;
            if (allowedOrigin !== "*" && allowedOrigin !== expectedOrigin) {
                console.warn(
                    `[HostChatBubbleRef] allowedOrigin="${allowedOrigin}" ≠ iframeUrl.origin="${expectedOrigin}".`
                );
            }

            const bubble = window.ZajunaBubble.create({
                iframeUrl,
                allowedOrigin,
                title,
                subtitle,
                position,
                startOpen,
                theme,
                zIndex,
                showLabel: false, // evita el “globo” superpuesto
                padding: 20, // respiro respecto al layout
                avatar, // avatar en el FAB (compacto o con label)
            });

            // 🔔 Canal de eventos del bubble
            bubble.onEvent((evt) => {
                setLastEvent(evt);
                if (evt?.type === "telemetry") {
                    onTelemetry?.(evt);
                } else if (evt?.type === "prefs:update") {
                    const next = {
                        theme: evt?.prefs?.theme || "light",
                        language: evt?.prefs?.language || "es",
                    };
                    setLastPrefs(next);
                    if (theme === "auto") {
                        document.documentElement.classList.toggle("dark", next.theme === "dark");
                    }
                } else if (evt?.type === "auth:needed") {
                    // 🔸 NO forzamos login: dejamos que el host decida (por defecto, ignoramos).
                    onAuthNeeded?.();
                }
            });

            bubble.mount();
            setMounted(true);

            // Token inicial si viene
            if (initialToken) bubble.sendAuthToken(initialToken);

            // ⛔️ Importante: NO abrir/cerrar automáticamente aquí.
            // (Se elimina cualquier ensureVisible que hacía open()->close()).

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
        ensureBubble,
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
        avatar,
    ]);

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
            // compat con tu código existente
            sendToken: (token) => bubbleRef.current?.sendAuthToken?.(token),
            // alias más explícito
            sendAuthToken: (token) => bubbleRef.current?.sendAuthToken?.(token),
            setTheme: (next) => {
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

    // Oculta panel de debug si no se pide
    if (!showDebug) return null;

    return (
        <div
            id="host-bubble-debug"
            style={{ position: "fixed", left: 8, bottom: 8, padding: 8, zIndex: zIndex + 1 }}
        >
            <div
                style={{
                    background: "rgba(15,23,42,.6)",
                    backdropFilter: "saturate(1.2) blur(4px)",
                    color: "#e5e7eb",
                    border: "1px solid #334155",
                    borderRadius: 12,
                    padding: 10,
                    minWidth: 260,
                }}
            >
                <div style={{ fontWeight: 600, marginBottom: 6 }}>HostChatBubbleRef (Debug)</div>
                {error ? (
                    <div style={{ fontSize: 12, color: "#fecaca", marginBottom: 8 }}>
                        <b>Error:</b> {error}
                        <div style={{ opacity: 0.8, marginTop: 4 }}>
                            Verifica <code>/embed/zajuna-bubble.js</code> y que{" "}
                            <code>allowedOrigin</code> coincida con el origen del iframe.
                        </div>
                    </div>
                ) : (
                    <div style={{ fontSize: 12, opacity: 0.9 }}>
                        <div>
                            mounted: <b>{String(mounted)}</b>
                        </div>
                        <div>
                            lastPrefs: theme=<b>{lastPrefs.theme}</b> lang=<b>{lastPrefs.language}</b>
                        </div>
                        <div>
                            lastEvent:{" "}
                            <code style={{ fontSize: 11 }}>
                                {lastEvent ? JSON.stringify(lastEvent) : "—"}
                            </code>
                        </div>
                    </div>
                )}

                <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <button onClick={() => bubbleRef.current?.open?.()} style={btn}>
                        Abrir
                    </button>
                    <button onClick={() => bubbleRef.current?.close?.()} style={btnSecondary}>
                        Cerrar
                    </button>
                    <button
                        onClick={() => {
                            const b = bubbleRef.current;
                            if (!b) return;
                            b.isOpen?.() ? b.close?.() : b.open?.();
                        }}
                        style={btn}
                    >
                        Toggle
                    </button>
                    <button
                        onClick={() => bubbleRef.current?.sendAuthToken?.("FAKE_TOKEN_ZAJUNA")}
                        style={btn}
                    >
                        Token FAKE
                    </button>
                    <button
                        onClick={() =>
                            bubbleRef.current?.setTheme?.(lastPrefs.theme === "dark" ? "light" : "dark")
                        }
                        style={btn}
                    >
                        Toggle theme
                    </button>
                    <button
                        onClick={() =>
                            bubbleRef.current?.setLanguage?.(lastPrefs.language === "es" ? "en" : "es")
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
const btnSecondary = { ...btn, background: "#1f2937", border: "1px solid #374151" };

export default HostChatBubbleRef;
