// admin_panel_react/src/rasa/meta.js
import { authState } from "../embed/authBridge.js";

/**
 * buildRasaMetadata
 *
 * @param {Object} opts
 * @param {boolean} [opts.isEmbed=true]      
 * @param {boolean} [opts.hasPanelToken=false] 
 */
export function buildRasaMetadata(opts = {}) {
    const {
        isEmbed = true,       
        hasPanelToken = false,
    } = opts;

    const hasEmbedToken = !!authState?.hasToken;
    const hasAnyToken = hasEmbedToken || hasPanelToken;

    return {
        auth: {
           
            hasToken: hasAnyToken,
            hasEmbedToken,
            hasPanelToken,
            // Si algún día necesitas enviar el token crudo del bridge:
            // embedToken: hasEmbedToken ? authState.token : undefined,
        },
        ui: {
            channel: isEmbed ? "web-embed" : "web-panel",
            version: "v1",
        },
    };
}
