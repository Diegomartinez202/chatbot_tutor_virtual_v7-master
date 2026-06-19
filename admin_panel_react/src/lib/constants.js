// src/lib/constants.js

// ====== API & Storage ======
export const API_BASE_URL = (
    import.meta?.env?.VITE_API_BASE_URL ||
    import.meta?.env?.VITE_API_URL ||
    // Fallback robusto: usa el origin actual + /api (sirve con Nginx en 8080)
    (typeof window !== "undefined" ? `${window.location.origin}/api` : "http://localhost:8080/api")
).replace(/\/$/, ""); // sin slash final

export const STORAGE_KEYS = {
    accessToken: "accessToken",
    refreshToken: "refreshToken", // si luego decides guardarlo (hoy NO)
    user: "authUser",
};

export const ROLES = {
    admin: "admin",
    soporte: "soporte",
    usuario: "usuario",
    tutor: "tutor", // opcional
};

export const DATE_FORMATS = {
    iso: "YYYY-MM-DD",
};

// ====== Colores (mapas simples) ======
export const STATUS_COLORS = {
    200: "green",
    201: "green",
    400: "yellow",
    401: "orange",
    403: "orange",
    404: "gray",
    500: "red",
};

export const ROLE_COLORS = {
    admin: "green",
    soporte: "purple",
    usuario: "gray",
    tutor: "blue",
};

export const INTENT_COLORS = {
    info: "blue",
    warning: "yellow",
    error: "red",
    soporte: "purple",
    soporte_intent: "purple",
    default: "gray",
};

// ====== Estilos (chips/badges) ======
export const ROLE_STYLES = {
    admin: "bg-purple-100 text-purple-800",
    soporte: "bg-blue-100 text-blue-800",
    usuario: "bg-gray-100 text-gray-800",
    user: "bg-gray-100 text-gray-800", // alias frecuente
    tutor: "bg-blue-100 text-blue-800",
};

export const STATUS_STYLES = {
    activo: "bg-green-100 text-green-800",
    inactivo: "bg-red-100 text-red-800",
    pendiente: "bg-yellow-100 text-yellow-800",
    ok: "bg-green-100 text-green-800",
    success: "bg-green-100 text-green-800",
    error: "bg-red-100 text-red-800",
    fail: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
};

export const INTENT_STYLES = {
    saludo: "bg-sky-100 text-sky-800",
    fallback: "bg-zinc-100 text-zinc-800",
    soporte_contacto: "bg-teal-100 text-teal-800",
    exito: "bg-green-100 text-green-800",  // añadido (no rompe)
    error: "bg-red-100 text-red-800",      // añadido (no rompe)
    default: "bg-gray-100 text-gray-800",
};
