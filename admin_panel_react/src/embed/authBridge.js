// admin_panel_react/src/embed/authBridge.js
export const authState = {
    hasToken: false,
    token: null, // si NO quieres usar el token crudo para nada, lo puedes ignorar
};

export function initAuthBridge(allowedOrigin = "*") {
    function isAllowed(origin) {
        if (!allowedOrigin || allowedOrigin === "*") return true;
        return origin === allowedOrigin;
    }

    window.addEventListener("message", (e) => {
        if (!isAllowed(e.origin)) return;
        const data = (e && e.data) || {};
        if (data && data.type === "auth:token") {
            authState.hasToken = !!data.token;
            authState.token = data.token || null;
            // Opcional: avisar al host que lo recibiste
            // window.parent?.postMessage({ type: "auth:received" }, "*");
        }
        if (data && data.type === "host:hello") {
            // el host nos saludó: puedes volver a pedir el token si te sirve
            try { window.parent && window.parent.postMessage({ type: "auth:request" }, "*"); } catch (e) { }
        }
    });

    // Nada más cargar el iframe, pide token al host
    try { window.parent && window.parent.postMessage({ type: "auth:request" }, "*"); } catch (e) { }
}
