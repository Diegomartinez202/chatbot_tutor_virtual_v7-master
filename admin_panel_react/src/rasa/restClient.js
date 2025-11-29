import { buildRasaMetadata } from "./meta.js";

const RASA_REST_URL = `${window.location.origin}/rasa/webhooks/rest/webhook`;

/**
 * @param {string} senderId
 * @param {string} text
 * @param {Object} [options]
 * @param {string} [options.authToken] - token del panel/admin (si existe)
 * @param {boolean} [options.isEmbed]  - si el chat está embebido
 */
export async function sendToRasaREST(senderId, text, options = {}) {
    const { authToken, isEmbed } = options || {};

    const metadata = buildRasaMetadata({
        isEmbed: typeof isEmbed === "boolean" ? isEmbed : true,
        hasPanelToken: !!authToken,
    });

    const body = {
        sender: String(senderId || "web"),
        message: String(text || ""),
        metadata,
    };

    try {
        const res = await fetch(RASA_REST_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                // ⚠️ Si ALGÚN día deciden enviar token de panel al backend de Rasa:
                // Authorization: authToken ? `Bearer ${authToken}` : undefined,
            },
            credentials: "include",
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            let detail = "";
            try {
                const data = await res.json();
                detail = data?.detail || "";
            } catch {
                // por si no es JSON
                detail = await res.text();
            }
         
            const err = new Error(detail || `Error REST ${res.status}`);
            err.status = res.status;
            throw err;
        }

        try {
            return await res.json();
        } catch (jsonErr) {
            throw new Error("Respuesta inválida del bot.");
        }

    } catch (err) {
       
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

        throw err;
    }
}
