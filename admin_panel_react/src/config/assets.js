// assets.js
// Centraliza rutas p�blicas servidas desde /public con BASE_URL estable
// Compatible con desarrollo (localhost) y producci�n (subcarpetas)

// Obtiene la base URL seg�n entorno
const getBaseUrl = () => {
    const baseEnv = import.meta.env?.BASE_URL;
    if (baseEnv) return baseEnv.replace(/\/+$/, "/");

    const origin = window.location.origin;
    const baseTag = document.querySelector("base")?.getAttribute("href") || "/";
    return new URL(baseTag, origin).href.replace(/\/+$/, "/");
};

const BASE = getBaseUrl();

// Funci�n para generar rutas absolutas de assets
const abs = (path) => {
    const cleanPath = path.replace(/^\/+/, "");
    try {
        return new URL(cleanPath, BASE).pathname;
    } catch {
        console.warn(`Ruta inv�lida: ${path}`);
        return cleanPath;
    }
};

// Assets centrales (manteniendo la l�gica original)
const assets = {
    BOT_AVATAR: abs("bot-avatar.png"),
    BOT_LOADING: abs("bot-loading.png"),
    USER_AVATAR: abs("favicon-32x32.png"), // opcional
};

export default assets;
export { abs, BASE };