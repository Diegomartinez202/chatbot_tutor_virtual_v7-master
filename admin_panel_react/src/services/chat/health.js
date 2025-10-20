// src/services/chat/health.js
import axios from "axios";

// Utilidades
function trimSlash(s) {
    return String(s || "").replace(/\/+$/, "");
}
function stripWebhook(path) {
    // Para Rasa REST: …/webhooks/rest/webhook -> base
    return String(path || "").replace(/\/webhooks\/rest\/webhook$/i, "");
}

async function tryGet(url) {
    const res = await axios.get(url, { timeout: 5000 });
    return res.status >= 200 && res.status < 500; // 404 no es "caída" del host
}

async function wsPing(wsUrl) {
    return new Promise((resolve, reject) => {
        try {
            const ws = new WebSocket(wsUrl);
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
 * - REST: prueba /health, /status, /live, /ready en el host
 * - WS: intenta abrir y cerrar el socket
 * No envía mensajes reales al bot.
 */
export async function connectChatHealth() {
    const mode = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();

    if (mode === "ws") {
        const wsUrl = import.meta.env.VITE_RASA_WS_URL;
        if (!wsUrl) throw new Error("VITE_RASA_WS_URL no configurado");
        await wsPing(wsUrl);
        return true;
    }

    // REST
    const restChatUrl = trimSlash(import.meta.env.VITE_CHAT_REST_URL || "");
    const rasaRest = trimSlash(import.meta.env.VITE_RASA_REST_URL || "");

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
