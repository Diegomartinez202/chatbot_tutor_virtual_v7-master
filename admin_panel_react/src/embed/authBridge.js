// admin_panel_react/src/embed/authBridge.js 
export const authState = {
    hasToken: false,
    token: null, 
};

export function initAuthBridge(allowedOrigin = "*") {
    function isAllowed(origin) {
        if (!allowedOrigin || allowedOrigin === "*") return true;
        return origin === allowedOrigin;
    }

    function getTargetOrigin() {
        if (allowedOrigin && allowedOrigin !== "*") return allowedOrigin;
        try {
            if (document.referrer) return new URL(document.referrer).origin;
        } catch { /* ignore */ }
        try {
            return (window.top && window.top.origin) || (window.parent && window.parent.origin) || "*";
        } catch { /* ignore */ }
        return "*"; 
    }
    function safePostToParent(msg) {
        try {
            const target = getTargetOrigin();
            window.parent?.postMessage(msg, target);
        } catch { /* ignore */ }
    }

    window.addEventListener("message", (e) => {
        if (!isAllowed(e.origin)) return;
        const data = (e && e.data) || {};
        if (data && data.type === "auth:token") {
            authState.hasToken = !!data.token;
            authState.token = data.token || null;

        }
        if (data && data.type === "host:hello") {

            safePostToParent({ type: "auth:request" });
        }
    });

    safePostToParent({ type: "auth:request" });
}
