// Centraliza rutas p�blicas servidas desde /public con BASE_URL estable
// Funciona en desarrollo (localhost) y producci�n (subcarpetas)
const getBaseUrl = () => {
    // Si Vite define BASE_URL, �sala
    if (import.meta.env?.BASE_URL) {
        return import.meta.env.BASE_URL.replace(/\/+$/, "/");
    }
    // Si no, construye la base desde el origen actual
    const origin = window.location.origin;
    // Extrae <base href> si existe
    const baseTag = document.querySelector("base")?.getAttribute("href") || "/";
    return new URL(baseTag, origin).href.replace(/\/+$/, "/");
};

const BASE = getBaseUrl();

// Resuelve rutas relativas contra BASE y garantiza un path �nico
const abs = (p) => new URL(p.replace(/^\/+/, ""), BASE).pathname;

const assets = {
    BOT_AVATAR: abs("bot-avatar.png"),
    BOT_LOADING: abs("bot-loading.png"),
    USER_AVATAR: abs("favicon-32x32.png"), // opcional
};

export default assets;