// src/services/axiosClient.js
import axios from "axios";
import { STORAGE_KEYS } from "@/lib/constants";
import { apiBase, apiUrl } from "@/lib/apiUrl";

/** Base URL segura (normalizada) */
const BASE_URL = apiBase();

/** Respeta cookies httpOnly (refresh) si tu backend las usa */
const WITH_CREDS = true;

const axiosClient = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
    withCredentials: WITH_CREDS,
});

// Aceptar JSON por defecto
axiosClient.defaults.headers.common.Accept = "application/json";

/* ─────────────────────────────────────────────────────────────
 * Manejo de refresh con cola para evitar condiciones de carrera
 * ────────────────────────────────────────────────────────────*/
let isRefreshing = false;
/** @type {Array<{resolve:(t:string|null)=>void, reject:(err:any)=>void}>} */
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token)));
    failedQueue = [];
};

/* ─────────────────────────────────────────────────────────────
 * Interceptor de REQUEST
 * - Inyecta Authorization si hay token
 * - Ajusta Content-Type sólo si no es FormData
 * ────────────────────────────────────────────────────────────*/
axiosClient.interceptors.request.use(
    (config) => {
        // Header Authorization (si no viene explícito)
        try {
            if (!config.headers?.Authorization) {
                const token = localStorage.getItem(STORAGE_KEYS.accessToken);
                if (token) {
                    config.headers = config.headers || {};
                    config.headers.Authorization = `Bearer ${token}`;
                }
            }
        } catch {
            // localStorage no disponible (SSR, iframes restringidos, etc.)
        }

        // Asegura Content-Type si mandamos JSON plano (no tocar FormData)
        if (config.data && typeof FormData !== "undefined" && !(config.data instanceof FormData)) {
            config.headers = config.headers || {};
            if (!config.headers["Content-Type"]) {
                config.headers["Content-Type"] = "application/json";
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

/* ─────────────────────────────────────────────────────────────
 * Interceptor de RESPONSE
 * - Si 401/403 y no es /auth/refresh, intenta refrescar token
 * - En paralelo, encola solicitudes hasta que termine el refresh
 * ────────────────────────────────────────────────────────────*/
axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Si no hay respuesta (network, CORS duro, timeout, etc.)
        if (!error?.response) return Promise.reject(error);

        const { config: originalRequest, response } = error;

        // Construye URL absoluta del refresh para comparar
        const refreshAbsolute = apiUrl("/auth/refresh");

        // Detecta si la request fallida es el refresh
        const originalAbs =
            ((originalRequest?.baseURL || "").replace(/\/$/, "")) + (originalRequest?.url || "");
        const isAuthRefreshCall =
            originalRequest?.url?.includes("/auth/refresh") || originalAbs === refreshAbsolute;

        // ¿Aplicamos refresh?
        const shouldTryRefresh =
            (response.status === 401 || response.status === 403) &&
            !originalRequest?._retry &&
            !isAuthRefreshCall;

        if (!shouldTryRefresh) {
            return Promise.reject(error);
        }

        originalRequest._retry = true;

        // Si ya hay un refresh en progreso, encolamos esta solicitud
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then((token) => {
                originalRequest.headers = originalRequest.headers || {};
                if (token) originalRequest.headers.Authorization = `Bearer ${token}`;
                return axiosClient(originalRequest);
            });
        }

        isRefreshing = true;

        try {
            // Hacemos el refresh con axios "plano" (no axiosClient) para evitar bucles
            const res = await axios.post(refreshAbsolute, {}, { withCredentials: WITH_CREDS });
            const newToken = res?.data?.access_token;
            if (!newToken) throw new Error("No se recibió access_token en el refresh.");

            // Persistimos y seteamos el header por defecto
            try {
                localStorage.setItem(STORAGE_KEYS.accessToken, newToken);
            } catch { }
            axiosClient.defaults.headers.common.Authorization = `Bearer ${newToken}`;

            // Despierta la cola
            processQueue(null, newToken);

            // Repite la request original con el nuevo token
            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return axiosClient(originalRequest);
        } catch (err) {
            // Falla el refresh: limpiamos token y rechazamos todo
            processQueue(err, null);
            try {
                localStorage.removeItem(STORAGE_KEYS.accessToken);
            } catch { }
            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);

/* ─────────────────────────────────────────────────────────────
 * Utilidades de token (por si quieres usarlas en otros módulos)
 * ────────────────────────────────────────────────────────────*/

/** Fija el token manualmente en el cliente y en localStorage. */
export function setAuthToken(token) {
    try {
        if (token) {
            localStorage.setItem(STORAGE_KEYS.accessToken, token);
            axiosClient.defaults.headers.common.Authorization = `Bearer ${token}`;
        } else {
            localStorage.removeItem(STORAGE_KEYS.accessToken);
            delete axiosClient.defaults.headers.common.Authorization;
        }
    } catch {
        // localStorage puede no estar disponible
        if (token) {
            axiosClient.defaults.headers.common.Authorization = `Bearer ${token}`;
        } else {
            delete axiosClient.defaults.headers.common.Authorization;
        }
    }
}

/** Limpia el token (helper) */
export function clearAuthToken() {
    setAuthToken(null);
}

/* ─────────────────────────────────────────────────────────────
 * Health-checks opcionales (no afectan tu flujo actual)
 * ────────────────────────────────────────────────────────────*/

/**
 * Health del API:
 * - Intenta /health
 * - Si 404/405, prueba "/" (algunos backends responden 200)
 * Nunca lanza: devuelve { ok, status, data|error, url }.
 */
export async function healthCheckApi({ signal } = {}) {
    const candidates = [
        apiUrl("/health"),
        apiUrl("/"),
        BASE_URL, // por si /health no existe
    ];

    for (const url of candidates) {
        try {
            const res = await axios.get(url, {
                withCredentials: WITH_CREDS,
                timeout: 5000,
                signal,
            });
            if (res.status >= 200 && res.status < 300) {
                return { ok: true, status: res.status, data: res.data, url };
            }
        } catch (e) {
            // continúa con el siguiente candidato
            if (e?.response) {
                // si hay respuesta pero no es 2xx, seguimos probando
            } else {
                // network/timeout: seguimos probando
            }
        }
    }
    return { ok: false, status: 0, error: "API health-check falló", url: candidates[candidates.length - 1] };
}

/**
 * Health del Chat:
 * - Si usas REST propio (VITE_CHAT_TRANSPORT=rest):
 *    · Prueba VITE_CHAT_REST_URL (GET) o variantes /health
 *    · Fallback: apiUrl('/chat/health') y apiUrl('/health')
 * - Si usas Rasa REST directo (VITE_RASA_REST_URL):
 *    · Prueba {rasaBase}/version (Rasa expone /version JSON)
 * Devuelve { ok, status, data|error, url }. NO lanza.
 */
export async function healthCheckChat({ signal } = {}) {
    const TRANSPORT = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();
    const REST = (import.meta.env.VITE_CHAT_REST_URL || "").trim();
    const RASA = (import.meta.env.VITE_RASA_REST_URL || "").trim();

    /** intenta una lista de URLs hasta que alguna responda 2xx */
    async function tryList(urls) {
        for (const url of urls) {
            if (!url) continue;
            try {
                const res = await axios.get(url, { timeout: 5000, signal });
                if (res.status >= 200 && res.status < 300) {
                    return { ok: true, status: res.status, data: res.data, url };
                }
            } catch {
                // seguimos probando
            }
        }
        return { ok: false, status: 0, error: "Chat health-check falló" };
    }

    if (TRANSPORT === "rest") {
        // Preferimos el endpoint REST declarado. Algunos backends aceptan GET simple.
        const baseRest = REST || apiUrl("/chat");
        const candidates = [
            baseRest, // GET directo (si responde 200)
            baseRest.replace(/\/$/, "") + "/health",
            apiUrl("/chat/health"),
            apiUrl("/health"),
            BASE_URL,
        ];
        return tryList(candidates);
    }

    // TRANSPORT === "ws" o uso de Rasa REST directo
    const rasaWebhook = RASA || ""; // p.ej. http://localhost:5005/webhooks/rest/webhook
    const rasaBase = rasaWebhook.replace(/\/webhooks\/rest\/webhook\/?$/, "");
    const candidates = [
        rasaBase ? rasaBase + "/version" : "",
        rasaBase, // GET raíz de Rasa devuelve HTML 200
    ];
    return tryList(candidates);
}

export default axiosClient;