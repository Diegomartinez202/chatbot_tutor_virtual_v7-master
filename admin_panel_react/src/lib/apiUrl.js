// src/lib/apiUrl.js
import { API_BASE_URL } from "@/lib/constants";

/**
 * Obtiene el objeto de variables de entorno según el runtime.
 * - En frontend (Vite): import.meta.env
 * - En Node / tests: process.env
 */
export function getEnv() {
    try {
        // En Vite existe import.meta.env
        return typeof import.meta !== "undefined" && import.meta?.env ? import.meta.env : {};
    } catch {
        // Fallback para Node/tests
        return typeof process !== "undefined" ? process.env ?? {} : {};
    }
}

/**
 * Devuelve la base normalizada (sin slash final).
 * Prioridad:
 *  1) API_BASE_URL desde constants (tu lógica de negocio original)
 *  2) VITE_API_BASE_URL | VITE_API_URL | VITE_CHAT_REST_URL (entornos)
 *  3) "/api" (fallback seguro)
 */
export function apiBase() {
    const env = getEnv();

    // Respeta tu constante primero (no rompemos tu lógica)
    const fromConstants = (API_BASE_URL || "").trim();
    const base =
        fromConstants ||
        env.VITE_API_BASE_URL ||
        env.VITE_API_URL ||
        env.VITE_CHAT_REST_URL ||
        "/api";

    return String(base).replace(/\/+$/, ""); // sin slash final
}

/**
 * Une base + path, quitando/añadiendo slashes donde toque.
 * - apiUrl() -> "https://api.tuapp.com"
 * - apiUrl("/auth/refresh") -> "https://api.tuapp.com/auth/refresh"
 * - apiUrl("auth/refresh")  -> "https://api.tuapp.com/auth/refresh"
 */
export function apiUrl(path = "") {
    const base = apiBase();
    const p = String(path || "").replace(/^\/+/, "");
    return p ? `${base}/${p}` : base;
}

/**
 * (Opcional) Une path + querystring desde un objeto de params.
 * Ej: buildUrl("/admin/logs", { page: 2, q: "hola" })
 * -> "https://api.tuapp.com/admin/logs?page=2&q=hola"
 */
export function buildUrl(path = "", params = {}) {
    const url = apiUrl(path);
    const entries = Object.entries(params).filter(
        ([, v]) => v !== undefined && v !== null && v !== ""
    );
    if (entries.length === 0) return url;

    const qs = new URLSearchParams(Object.fromEntries(entries)).toString();
    return `${url}?${qs}`;
}