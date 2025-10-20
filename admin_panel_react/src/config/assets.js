// Centraliza rutas públicas servidas desde /public con BASE_URL estable
const BASE = (import.meta.env?.BASE_URL ?? window.location.origin + "/").replace(/\/+$/, "/");

// Resuelve contra <base href> y garantiza un path único (soporta subcarpetas)
const abs = (p) => new URL(p.replace(/^\/+/, ""), BASE).pathname;

const assets = {
    BOT_AVATAR: abs("bot-avatar.png"),
    BOT_LOADING: abs("bot-loading.png"),
    USER_AVATAR: abs("favicon-32x32.png"), // opcional
};

export default assets;