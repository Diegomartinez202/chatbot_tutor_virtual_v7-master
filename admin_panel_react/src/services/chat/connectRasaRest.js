// src/services/chat/connectRasaRest.js

/**
 * URL base del REST proxy del backend (FastAPI) hacia Rasa.
 * - Por defecto usamos /api/chat (proxy recomendado).
 * - Puedes sobreescribir con VITE_CHAT_REST_URL o pasando { baseUrl }.
 */
export const DEFAULT_CHAT_URL =
    (import.meta?.env?.VITE_CHAT_REST_URL && String(import.meta.env.VITE_CHAT_REST_URL).trim()) ||
    "/api/chat";

/**
 * Healthcheck simple contra tu backend (alias a Rasa).
 * GET <baseUrl>/health → OK si responde 2xx.
 *
 * @param {Object} opts
 * @param {string} [opts.baseUrl]   - Base URL del chat (ej: "/api/chat" o "https://.../api/chat")
 * @param {string} [opts.token]     - Token Bearer para Authorization
 * @param {string} [opts.healthUrl] - URL absoluta para health, si no deriva de baseUrl
 * @returns {Promise<boolean>}
 */
export async function connectRasaRest(opts = {}) {
    const base = String(opts.baseUrl || DEFAULT_CHAT_URL).replace(/\/$/, "");
    const healthUrl = opts.healthUrl || `${base}/health`;

    const headers = {};
    const token =
        opts.token ||
        (typeof localStorage !== "undefined" ? localStorage.getItem("zajuna_token") : null);
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(healthUrl, {
        method: "GET",
        headers,
        credentials: "include", // 👈 por si usas cookie HttpOnly
    });
    if (!res.ok) throw new Error(`Healthcheck failed: ${res.status}`);
    return true;
}

/**
 * Envía un mensaje al backend (proxy REST → Rasa).
 * Body compatible con rutas antiguas y nuevas: { text, message, sender, metadata }.
 * Adjunta Authorization: Bearer <token> si existe.
 *
 * @param {Object} params
 * @param {string} params.text                  - Texto o payload ("/intent{...}")
 * @param {string} [params.sender]              - ID del usuario/sender
 * @param {Object} [params.metadata={}]         - Metadatos para tracker.latest_message.metadata
 * @param {string} [params.baseUrl]             - Override del endpoint (por defecto DEFAULT_CHAT_URL)
 * @param {string} [params.token]               - Token Bearer (si no, usa localStorage.zajuna_token)
 * @returns {Promise<Array>}                    - Array de mensajes Rasa [{ text?, image?, ... }]
 */
export async function sendRasaMessage({ text, sender, metadata = {}, baseUrl, token } = {}) {
    if (!text || !String(text).trim()) {
        throw new Error("Mensaje vacío");
    }

    const host = String(baseUrl || DEFAULT_CHAT_URL).replace(/\/$/, "");
    const authToken =
        token || (typeof localStorage !== "undefined" ? localStorage.getItem("zajuna_token") : null);

    const headers = { "Content-Type": "application/json" };
    if (authToken) headers.Authorization = `Bearer ${authToken}`;

    const body = {
        // compat: algunos backends esperan `message`, otros `text`
        text,
        message: text,
        sender: sender || getOrCreateSenderId(),
        metadata: {
            ...metadata,
            auth: { hasToken: !!authToken },
        },
    };

    const res = await fetch(host, {
        method: "POST",
        headers,
        credentials: "include", // 👈 por si usas cookie HttpOnly
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(`REST ${res.status}: ${msg || "error al enviar mensaje"}`);
    }

    const data = await res.json().catch(() => []);
    return Array.isArray(data) ? data : [];
}

// —— Helpers —— //
const SENDER_KEY = "chat_sender_id";
function getOrCreateSenderId() {
    try {
        const existing = localStorage.getItem(SENDER_KEY);
        if (existing) return existing;
        const id = `web-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
        localStorage.setItem(SENDER_KEY, id);
        return id;
    } catch {
        // Fallback no persistente si localStorage no está disponible
        return `web-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
    }
}
