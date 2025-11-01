// src/utils/telemetry.js
export function trackLink(url, extra = {}) {
    try {
        const payload = JSON.stringify({
            ev: "link_open",
            url: String(url || ""),
            ts: Date.now(),
            ...extra,
        });

        // Enviar como Beacon si existe (no bloquea la navegación)
        if (navigator?.sendBeacon) {
            const blob = new Blob([payload], { type: "application/json" });
            const ok = navigator.sendBeacon("/api/telemetry", blob);
            if (ok) return true;
        }

        // Fallback a fetch "fire-and-forget"
        fetch("/api/telemetry", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            keepalive: true,
            body: payload,
        }).catch(() => { });
    } catch {
        // no-op
    }
    return false;
}
