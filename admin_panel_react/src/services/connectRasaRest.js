// src/services/connectRasaRest.js
import axios from "axios";

/**
 * Escoge el endpoint REST desde .env con fallback:
 * 1) VITE_CHAT_REST_URL (tu backend /api/chat)
 * 2) VITE_RASA_REST_URL (webhook de Rasa: http://localhost:5005/webhooks/rest/webhook)
 * 3) /api/chat (fallback)
 */
function getRestEndpoint() {
    const url =
        import.meta.env.VITE_CHAT_REST_URL ||
        import.meta.env.VITE_RASA_REST_URL ||
        "/api/chat";
    return String(url);
}

/**
 * Envía mensaje de usuario al backend REST y devuelve la respuesta estándar:
 * [{ text, ... }, ...]
 */
export async function sendRasaMessage({ sender, message, metadata }) {
    const endpoint = getRestEndpoint();

    try {
        const { data } = await axios.post(endpoint, {
            sender: sender || "web_user",
            message,
            metadata: metadata || {},
        });

        // Normaliza respuesta: Rasa devuelve array de objetos; tu API podría
        // devolver { replies: [...] }. Conservamos ambos sin romper tu lógica.
        if (Array.isArray(data)) return data;
        if (Array.isArray(data?.replies)) return data.replies;

        return [{ text: String(data?.text || "Sin respuesta") }];
    } catch (err) {
        const status = err?.response?.status;
        const detail = err?.response?.data || err?.message;
        console.error(`REST ${status || ""}:`, detail);
        throw new Error(`REST ${status || ""}: error al enviar mensaje`);
    }
}