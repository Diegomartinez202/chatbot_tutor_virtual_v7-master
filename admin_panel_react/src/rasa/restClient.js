// admin_panel_react/src/rasa/restClient.js
import { buildRasaMetadata } from "./meta.js";

const RASA_REST_URL = `${window.location.origin}/rasa/webhooks/rest/webhook`;

export async function sendToRasaREST(senderId, text) {
    const body = {
        sender: String(senderId || "web"),
        message: String(text || ""),
        metadata: buildRasaMetadata(),
    };

    try {
        const res = await fetch(RASA_REST_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(body),
        });

        // ⛔ Si la respuesta NO es OK, procesamos el error real
        if (!res.ok) {
            let detail = "";
            try {
                const data = await res.json();
                detail = data?.detail || "";
            } catch {
                // por si no es JSON
                detail = await res.text();
            }

            // Construimos un error más informativo hacia arriba
            const err = new Error(detail || `Error REST ${res.status}`);
            err.status = res.status;
            throw err;
        }

        // ⛔ Si no es JSON válido
        try {
            return await res.json();
        } catch (jsonErr) {
            throw new Error("Respuesta inválida del bot.");
        }

    } catch (err) {
        // ⛔ Error de red (proxy caído, timeout, CORS, caída del bot...)
        if (err?.message?.includes("proxy_network_error")) {
            const friendly = new Error(
                "El servidor del bot no responde en este momento. Inténtalo nuevamente."
            );
            friendly.code = "BOT_PROXY_ERROR";
            throw friendly;
        }

        if (err.message.includes("Failed to fetch")) {
            const friendly = new Error(
                "No hay conexión con el servidor del bot."
            );
            friendly.code = "NETWORK_DOWN";
            throw friendly;
        }

        // Re-lanzamos error normal
        throw err;
    }
}
