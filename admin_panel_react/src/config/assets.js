// assets.js
// Centraliza rutas p�blicas servidas desde /public
// Compatible con desarrollo, producci�n en subcarpetas y entornos sin BASE_URL

const getBaseUrl = () => {
    try {
        // Vite define BASE_URL en import.meta.env
        const baseEnv = import.meta.env?.BASE_URL || "/";
        return baseEnv.replace(/\/+$/, "/"); // eliminar barras al final
    } catch {
        // Fallback si import.meta.env no est� disponible (ej: entornos especiales)
        const origin = window.location.origin;
        const baseTag = document.querySelector("base")?.getAttribute("href") || "/";
        return new URL(baseTag, origin).href.replace(/\/+$/, "/");
    }
};

const BASE = getBaseUrl();

// Funci�n para generar rutas absolutas de assets
const abs = (path) => {
    const cleanPath = path.replace(/^\/+/, ""); // eliminar barras al inicio
    try {
        return `${BASE}${cleanPath}`;
    } catch {
        console.warn(`Ruta inv�lida: ${path}`);
        return cleanPath;
    }
};

// Assets centrales
const assets = {
    BOT_AVATAR: abs("bot-avatar.png"),
    BOT_LOADING: abs("bot-loading.png"),
    USER_AVATAR: abs("favicon-32x32.png"),
};

export default assets;
export { abs, BASE };