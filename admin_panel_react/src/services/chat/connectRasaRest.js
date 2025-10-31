// src/services/chat/connectRasaRest.js

// 👉 Base API del backend (no Rasa directo). Si no viene por env, usa http://localhost:8000
const API_BASE = (import.meta?.env?.VITE_API_BASE && String(import.meta.env.VITE_API_BASE).trim())
    || "http://localhost:8000";

// 👉 Endpoint REST del proxy hacia Rasa en tu backend
export const RASA_PROXY_URL = `${API_BASE.replace(/\/$/, "")}/chat/rasa/rest/webhook`;

// (opcional) health si lo necesitas en otros lugares del front
export const DEFAULT_CHAT_HEALTH =
    (import.meta?.env?.VITE_CHAT_REST_URL && String(import.meta.env.VITE_CHAT_REST_URL).trim())
    || `${API_BASE.replace(/\/$/, "")}/chat/health`;

/**
 * Healthcheck simple contra tu backend (alias a Rasa).
 * GET <healthUrl> → OK si responde 2xx.
 */
export async function connectRasaRest(opts = {}) {
    const healthUrl = String(opts.healthUrl || DEFAULT_CHAT_HEALTH);
    const headers = {};
    const token =
        opts.token ||
        (typeof localStorage !== "undefined" ? localStorage.getItem("zajuna_token") : null);
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(healthUrl, {
        method: "GET",
        headers,
        credentials: "include",
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
 * @param {string} params.text          Texto o payload ("/intent{...}")
 * @param {string} [params.sender]      ID del usuario/sender
 * @param {Object} [params.metadata={}] Metadatos para tracker.latest_message.metadata
 * @param {string} [params.token]       Token Bearer (si no, usa localStorage.zajuna_token)
 * @returns {Promise<Array>}            Array de mensajes Rasa [{ text?, image?, buttons?, ... }]
 */
export async function sendRasaMessage({ text, sender, metadata = {}, token } = {}) {
    if (!text || !String(text).trim()) throw new Error("Mensaje vacío");

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
            auth: { hasToken: !!authToken }, // <- clave para ActionCheckAuth
        },
    };

    const res = await fetch(RASA_PROXY_URL, {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(`RASA REST ${res.status}: ${msg || "error al enviar mensaje"}`);
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
