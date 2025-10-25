// src/services/chat/health.js
import axios from "axios";

// Utilidades
function trimSlash(s) {
    return String(s || "").replace(/\/+$/, "");
}
function stripWebhook(path) {
    // Para Rasa REST: …/webhooks/rest/webhook -> base
    return String(path || "").replace(/\/webhooks\/rest\/webhook\/?$/i, "");
}

function toAbsoluteWs(urlLike) {
    const raw = String(urlLike || "").trim();
    if (!raw) throw new Error("WS URL vacío");

    // Si ya es ws:// o wss:// lo usamos tal cual
    if (/^wss?:\/\//i.test(raw)) return raw;

    // Si es http(s)://... lo convertimos a ws(s)://...
    if (/^https?:\/\//i.test(raw)) {
        return raw.replace(/^http/i, "ws");
    }

    // Si es relativo ("/ws" o "ws"), armamos con el host actual
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.host;

    if (raw.startsWith("/")) {
        return `${proto}://${host}${raw}`;
    }
    // relativo sin "/": lo pegamos al origen
    return `${proto}://${host}/${raw.replace(/^\/+/, "")}`;
}

async function tryGet(url) {
    const res = await axios.get(url, { timeout: 5000 });
    // 2xx / 3xx / incluso 404 nos sirven para saber que el host responde
    return res.status >= 200 && res.status < 500;
}

async function wsPing(wsUrl) {
    const abs = toAbsoluteWs(wsUrl);
    return new Promise((resolve, reject) => {
        try {
            const ws = new WebSocket(abs);
            const timer = setTimeout(() => {
                try { ws.close(); } catch { }
                reject(new Error("WS timeout"));
            }, 5000);

            ws.onopen = () => {
                clearTimeout(timer);
                try { ws.close(); } catch { }
                resolve(true);
            };
            ws.onerror = (e) => {
                clearTimeout(timer);
                reject(e || new Error("WS error"));
            };
        } catch (e) {
            reject(e);
        }
    });
}

/**
 * Health universal del chat:
 * - WS: intenta abrir/cerrar el socket (no envía mensajes)
 * - REST: prueba /health, /status, /live, /ready en el host
 */
export async function connectChatHealth() {
    const mode = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();

    if (mode === "ws") {
        const wsUrl = import.meta.env.VITE_RASA_WS_URL || import.meta.env.VITE_RASA_WS || "/ws";
        await wsPing(wsUrl);
        return true;
    }

    // REST
    const restChatUrl = trimSlash(import.meta.env.VITE_CHAT_REST_URL || "/api/chat");
    const rasaRest = trimSlash(import.meta.env.VITE_RASA_REST_URL || import.meta.env.VITE_RASA_HTTP || "");

    const candidates = [];

    // Si pasas por tu API: intentar en el host /health (y variantes)
    if (restChatUrl) {
        const base = restChatUrl.includes("/api/chat")
            ? restChatUrl.replace(/\/api\/chat$/i, "")
            : restChatUrl;
        candidates.push(`${base}/health`);
        candidates.push(`${base}/status`);
        candidates.push(`${base}/live`);
        candidates.push(`${base}/ready`);
    }

    // Si apuntas directo a Rasa REST
    if (rasaRest) {
        const base = stripWebhook(rasaRest);
        candidates.push(`${base}/status`);
        candidates.push(`${base}/health`);
    }

    // Fallback local por si estás desarrollando
    if (candidates.length === 0) {
        candidates.push("/api/health");
    }

    // Probar en orden
    let lastErr = null;
    for (const url of candidates) {
        try {
            const ok = await tryGet(url);
            if (ok) return true;
        } catch (e) {
            lastErr = e;
        }
    }
    throw lastErr || new Error("No se pudo verificar el estado del chat.");
}