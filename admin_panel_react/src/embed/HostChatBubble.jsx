/** admin_panel_react/src/embed/HostChatBubble.jsx */
import React, { useCallback, useEffect, useRef, useState } from "react";

export default function HostChatBubble({
    iframeUrl = `${window.location.origin}/?embed=1`,
    allowedOrigin = window.location.origin,
    title = "Tutor Virtual",
    subtitle = "Sustentación",
    position = "bottom-right", // bottom-right | bottom-left | top-right | top-left
    startOpen = false,         // NO forzamos abrir
    theme = "auto",            // auto | light | dark
    zIndex = 2147483000,
    initialToken,
    onTelemetry,
    onAuthNeeded,
    // 🆕 Opcionales añadidos: avatares (NO rompen nada si no se usan)
    avatar = import.meta?.env?.VITE_BOT_AVATAR || "/bot-avatar.png",
    loadingAvatar = import.meta?.env?.VITE_BOT_LOADING || "/bot-loading.png",
}) {
    const bubbleRef = useRef(null);
    const [mounted, setMounted] = useState(false);
    const [lastPrefs, setLastPrefs] = useState({ theme: "light", language: "es" });
    const [lastEvent, setLastEvent] = useState(null);
    const [error, setError] = useState("");

    // 🆕 Persistencia local (no afecta si no existe soporte en el bubble)
    const LS_OPEN = "zj_bubble_open";
    const LS_MIN = "zj_bubble_min";
    const savedOpen = (typeof window !== "undefined" && localStorage.getItem(LS_OPEN) === "1");
    const savedMin = (typeof window !== "undefined" && localStorage.getItem(LS_MIN) === "1");

    // 🆕 allowedOrigin efectivo: usamos el real del iframe si es posible (origin estricto)
    const effectiveAllowedOrigin = (() => {
        try { return new URL(iframeUrl, window.location.href).origin; }
        catch { return allowedOrigin; }
    })();

    // Carga segura del script del bubble
    const ensureBubbleScript = useCallback(() => {
        return new Promise((resolve, reject) => {
            if (window.ZajunaBubble?.create) return resolve(true);
            const existing = document.getElementById("zj-bubble-script");
            if (existing) {
                existing.addEventListener("load", () => resolve(true), { once: true });
                existing.addEventListener("error", reject, { once: true });
                return;
            }
            const s = document.createElement("script");
            s.id = "zj-bubble-script";
            s.src = "/embed/zajuna-bubble.js";
            s.async = true;
            s.onload = () => resolve(true);
            s.onerror = (e) => reject(e);
            document.head.appendChild(s);
        });
    }, []);

    useEffect(() => {
        let destroyed = false;

        (async () => {
            try {
                await ensureBubbleScript();
                if (destroyed) return;

                if (!window.ZajunaBubble?.create) {
                    throw new Error("[HostChatBubble] ZajunaBubble.create no disponible");
                }

                // crea instancia del bubble (el iframe y el botón los gestiona el script)
                // 🔒 usamos effectiveAllowedOrigin y también añadimos avatar/showLabel sin romper compat
                const bubble = window.ZajunaBubble.create({
                    iframeUrl,
                    allowedOrigin: effectiveAllowedOrigin, // <- origin estricto del iframe
                    title,
                    subtitle,
                    position,
                    startOpen: (savedOpen ?? startOpen),   // 🆕 respeta persistencia si existe
                    theme,
                    zIndex,
                    // 🆕 extras no disruptivos:
                    showLabel: false,  // si tu CSS/JS ya maneja compact, esto no rompe nada
                    avatar,            // avatar del FAB si tu bubble lo soporta
                });

                // escucha eventos del iframe
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
                        onAuthNeeded?.();
                    }

                    // 🆕 Persistencia si el bubble emite estos eventos (no molesta si no existen)
                    if (evt?.type === "widget:opened") { try { localStorage.setItem(LS_OPEN, "1"); } catch { } }
                    if (evt?.type === "widget:closed") { try { localStorage.setItem(LS_OPEN, "0"); } catch { } }
                    if (evt?.type === "widget:min") { try { localStorage.setItem(LS_MIN, "1"); } catch { } }
                    if (evt?.type === "widget:restore") { try { localStorage.setItem(LS_MIN, "0"); } catch { } }

                    // 🆕 “Typing”: si el bubble reenvía {type:'bot:typing', active:true|false}
                    if (evt?.type === "bot:typing") {
                        const on = !!evt.active;
                        if (typeof bubble.setAvatar === "function") {
                            bubble.setAvatar(on ? loadingAvatar : avatar);
                        } else {
                            // fallback: intenta cambiar el <img> del FAB si está marcado en el DOM
                            const img = document.querySelector('[data-zj-fab] img');
                            if (img) img.src = on ? loadingAvatar : avatar;
                        }
                    }
                });

                bubble.mount();
                setMounted(true);

                // envía token si viene
                if (initialToken) bubble.sendAuthToken(initialToken);

                // 🆕 restaurar minimizado si el bubble expone minimize(true)
                if (savedOpen && savedMin && typeof bubble.minimize === "function") {
                    bubble.minimize(true);
                }

                bubbleRef.current = bubble;
            } catch (e) {
                setError(String(e?.message || e));
            }
        })();

        return () => {
            destroyed = true;
            try { bubbleRef.current?.unmount?.(); } catch { }
            bubbleRef.current = null;
            setMounted(false);
        };
    }, [
        ensureBubbleScript,
        iframeUrl,
        allowedOrigin,
        effectiveAllowedOrigin, // 🆕
        title,
        subtitle,
        position,
        startOpen,
        theme,
        zIndex,
        initialToken,
        onTelemetry,
        onAuthNeeded,
        avatar,          // 🆕
        loadingAvatar,   // 🆕
        savedOpen, savedMin, // 🆕
    ]);

    // API de conveniencia
    const sendToken = useCallback((token) => {
        bubbleRef.current?.sendAuthToken?.(token);
    }, []);
    const setTheme = useCallback(
        (next) => {
            bubbleRef.current?.setTheme?.(next);
            if (theme === "auto") {
                document.documentElement.classList.toggle("dark", next === "dark");
            }
        },
        [theme]
    );
    const setLanguage = useCallback((lang) => {
        bubbleRef.current?.setLanguage?.(lang);
    }, []);

    // UI mínima de debug (puedes ocultarla al integrarlo en prod)
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

                {error ? (
                    <div style={{ fontSize: 12, color: "#fecaca" }}>
                        <b>Error:</b> {error}
                        <div style={{ opacity: 0.8, marginTop: 6 }}>
                            Verifica que <code>/embed/zajuna-bubble.js</code> esté accesible.
                        </div>
                    </div>
                ) : (
                    <div style={{ fontSize: 12, opacity: 0.9 }}>
                        <div>mounted: <b>{String(mounted)}</b></div>
                        <div>lastPrefs: theme=<b>{lastPrefs.theme}</b> lang=<b>{lastPrefs.language}</b></div>
                        <div>lastEvent: <code style={{ fontSize: 11 }}>{lastEvent ? JSON.stringify(lastEvent) : "—"}</code></div>
                    </div>
                )}

                <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <button onClick={() => bubbleRef.current?.open?.()} style={btn}>Abrir</button>
                    <button onClick={() => bubbleRef.current?.close?.()} style={btnSecondary}>Cerrar</button>
                    <button onClick={() => sendToken("FAKE_TOKEN_ZAJUNA")} style={btn}>Token FAKE</button>
                    <button
                        onClick={() => setTheme(lastPrefs.theme === "dark" ? "light" : "dark")}
                        style={btn}
                    >
                        Toggle theme
                    </button>
                    <button
                        onClick={() => setLanguage(lastPrefs.language === "es" ? "en" : "es")}
                        style={btnSecondary}
                    >
                        Toggle lang
                    </button>
                </div>
            </div>
        </div>
    );
}

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
