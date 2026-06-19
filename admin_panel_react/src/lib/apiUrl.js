import { API_BASE_URL } from "@/lib/constants";

/** Env seguro */
export function getEnv() {
    try {
        return typeof import.meta !== "undefined" && import.meta?.env ? import.meta.env : {};
    } catch {
        return typeof process !== "undefined" ? process.env ?? {} : {};
    }
}

/**
 * Base del API (FastAPI) — SIN mezclar variables del chat
 * Prioridad:
 *  1) API_BASE_URL (constants)
 *  2) VITE_API_BASE | VITE_API_BASE_URL | VITE_API_URL
 *  3) "/api"
 */
export function apiBase() {
    const env = getEnv();
    const base =
        (API_BASE_URL || "").trim() ||
        (env.VITE_API_BASE || "").trim() ||
        (env.VITE_API_BASE_URL || "").trim() ||
        (env.VITE_API_URL || "").trim() ||
        "/api";
    return String(base).replace(/\/+$/, "");
}

/** Une base + path (evita dobles slashes) */
export function apiUrl(path = "") {
    const base = apiBase();
    const p = String(path || "").replace(/^\/+/, "");
    return p ? `${base}/${p}` : base;
}

/** (Opcional) URL con querystring */
export function buildUrl(path = "", params = {}) {
    const url = apiUrl(path);
    const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
    if (entries.length === 0) return url;
    const qs = new URLSearchParams(Object.fromEntries(entries)).toString();
    return `${url}?${qs}`;
}

/* ======== SUGERENCIA: base del CHAT separada ======== */
/** Base del Chat (Rasa REST o proxy) */
export function chatBase() {
    const env = getEnv();
    const base =
        (env.VITE_CHAT_REST_URL || "").trim() ||            // ej. http://localhost:8080/api/chat/rasa/rest/webhook
        `${apiBase()}/chat`;                                 // proxy por FastAPI (tu lógica actual)
    return String(base).replace(/\/+$/, "");
}

