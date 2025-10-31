// admin_panel_react/src/rasa/restClient.js
import { buildRasaMetadata } from "./meta.js";

// Ajusta a tu ruta real:
// - Directo a Rasa: "http://localhost:5005/webhooks/rest/webhook"
// - Vía tu backend proxy: `${window.location.origin}/rasa/webhooks/rest/webhook`
const RASA_REST_URL = `${window.location.origin}/rasa/webhooks/rest/webhook`;

export async function sendToRasaREST(senderId, text) {
    const body = {
        sender: String(senderId || "web"),
        message: String(text || ""),
        metadata: buildRasaMetadata(),
    };

    const res = await fetch(RASA_REST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // si usas cookies httpOnly
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        throw new Error(`REST ${res.status}`);
    }
    return res.json(); // array de mensajes del bot
}
