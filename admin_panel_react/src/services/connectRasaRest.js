// src/services/connectRasaRest.js
// 🔁 Adaptador de compatibilidad. Reusa el módulo canónico del chat.

import {
    DEFAULT_CHAT_URL,
    connectRasaRest as _connectRasaRest,
    sendRasaMessage as _sendRasaMessage,
} from "./chat/connectRasaRest";

/**
 * Conexión/health (reexport)
 */
export const DEFAULT_CHAT_URL_COMPAT = DEFAULT_CHAT_URL;
export async function connectRasaRest(opts = {}) {
    return _connectRasaRest(opts);
}

/**
 * En algunos sitios antiguos se llama con { sender, message, metadata }.
 * Aquí adaptamos a la firma moderna { text, sender, metadata }.
 */
export async function sendRasaMessage(params = {}) {
    const { sender, message, text, metadata, baseUrl, token } = params;
    const payload = {
        text: text || message || "",
        sender,
        metadata,
        baseUrl,
        token,
    };
    return _sendRasaMessage(payload);
}
