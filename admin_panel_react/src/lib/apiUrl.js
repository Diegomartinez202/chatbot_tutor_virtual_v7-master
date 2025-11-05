// src/lib/apiUrl.js
import { API_BASE_URL } from "@/lib/constants";

/** Obtiene variables de entorno según el runtime. */
export function getEnv() {
    try {
        return typeof import.meta !== "undefined" && import.meta?.env ? import.meta.env : {};
    } catch {
        return typeof process !== "undefined" ? process.env ?? {} : {};
    }
}

/**
 * Base normalizada (sin slash final).
 * Prioridad:
 *  1) API_BASE_URL (constants)  ✅ respeta tu negocio
 *  2) VITE_API_BASE_URL | VITE_API_URL | VITE_CHAT_REST_URL
 *  3) "/api" (fallback seguro)
 */
export function apiBase() {
    const env = getEnv();
    const fromConstants = (API_BASE_URL || "").trim();
    const base =
        fromConstants ||
        env.VITE_API_BASE_URL ||
        env.VITE_API_URL ||
        env.VITE_CHAT_REST_URL ||
        "/api";

    return String(base).replace(/\/+$/, ""); // sin slash final
}

/** Une base + path (evita dobles slashes). */
export function apiUrl(path = "") {
    const base = apiBase();
    const p = String(path || "").replace(/^\/+/, "");
    return p ? `${base}/${p}` : base;
}

/** (Opcional) Construye URL con querystring. */
export function buildUrl(path = "", params = {}) {
    const url = apiUrl(path);
    const entries = Object.entries(params).filter(
        ([, v]) => v !== undefined && v !== null && v !== ""
    );
    if (entries.length === 0) return url;

    const qs = new URLSearchParams(Object.fromEntries(entries)).toString();
    return `${url}?${qs}`;
}
