// src/services/chat/connectWS.js

function toAbsoluteWs(urlLike) {
    const raw = String(urlLike || "").trim();
    if (!raw) throw new Error("wsUrl requerido");

    // Si ya es ws:// o wss://
    if (/^wss?:\/\//i.test(raw)) return raw;

    // Si es http(s)://... lo convertimos a ws(s)://...
    if (/^https?:\/\//i.test(raw)) {
        return raw.replace(/^http/i, "ws");
    }

    // Si es relativo, armamos con el origen actual
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.host;

    if (raw.startsWith("/")) {
        return `${proto}://${host}${raw}`;
    }
    // relativo sin "/"
    return `${proto}://${host}/${raw.replace(/^\/+/, "")}`;
}

/**
 * Conecta a un WebSocket y resuelve cuando abre.
 * Útil como connectFn para ChatWidget/ChatPage (solo health).
 */
export function connectWS({ wsUrl, token, protocols, timeoutMs = 5000 } = {}) {
    return new Promise((resolve, reject) => {
        try {
            if (!wsUrl) return reject(new Error("wsUrl requerido"));

            const abs = toAbsoluteWs(wsUrl);

            // Token por querystring si viene
            const url = new URL(abs);
            if (token && !url.searchParams.get("token")) {
                url.searchParams.set("token", token);
            }

            const ws = new WebSocket(url.toString(), protocols);
            const timer = setTimeout(() => {
                try { ws.close(); } catch { }
                reject(new Error("timeout"));
            }, timeoutMs);

            ws.onopen = () => {
                clearTimeout(timer);
                try { ws.close(); } catch { }
                resolve(true);
            };
            ws.onerror = (e) => {
                clearTimeout(timer);
                reject(e instanceof Error ? e : new Error("WebSocket error"));
            };
        } catch (e) {
            reject(e);
        }
    });
}

/**
 * Cliente WS completo para enviar/recibir mensajes del chat.
 * - Devuelve { ws, sendText, sendJson, close }
 * - Puedes pasar onMessage(ev) para manejar eventos entrantes
 * - Mantiene keepAlive ping opcional
 */
export function createWSClient({
    wsUrl,
    token,
    protocols,
    onMessage,
    timeoutMs = 8000,
    keepAliveMs = 30000,
} = {}) {
    if (!wsUrl) throw new Error("wsUrl requerido");

    const abs = toAbsoluteWs(wsUrl);
    const url = new URL(abs);
    if (token && !url.searchParams.get("token")) {
        url.searchParams.set("token", token);
    }

    const ws = new WebSocket(url.toString(), protocols);
    let pingTimer = null;

    const ready = new Promise((resolve, reject) => {
        const t = setTimeout(() => reject(new Error("timeout")), timeoutMs);
        ws.onopen = () => {
            clearTimeout(t);
            if (keepAliveMs > 0) {
                pingTimer = setInterval(() => {
                    try {
                        ws.send(JSON.stringify({ type: "ping", t: Date.now() }));
                    } catch { }
                }, keepAliveMs);
            }
            resolve(true);
        };
        ws.onerror = (e) => {
            clearTimeout(t);
            reject(e instanceof Error ? e : new Error("WebSocket error"));
        };
    });

    ws.onmessage = (ev) => {
        try {
            onMessage && onMessage(ev);
        } catch { }
    };

    const sendJson = (obj) => {
        ws.send(JSON.stringify(obj));
    };
    const sendText = (text) => {
        ws.send(text);
    };
    const close = () => {
        try { ws.close(); } catch { }
        if (pingTimer) {
            clearInterval(pingTimer);
            pingTimer = null;
        }
    };

    return { ws, ready, sendJson, sendText, close };
}