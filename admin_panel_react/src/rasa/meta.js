// admin_panel_react/src/rasa/meta.js
import { authState } from "../embed/authBridge.js";

export function buildRasaMetadata() {
    return {
        auth: {
            hasToken: !!authState.hasToken,
            // Si algún día necesitas enviar el token crudo:
            // token: authState.token
        },
        ui: {
            channel: "web-embed",
            version: "v1",
        },
    };
}
