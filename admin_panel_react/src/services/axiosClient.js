// src/services/axiosClient.js
import axios from "axios";
import { STORAGE_KEYS } from "@/lib/constants";
import { apiBase, apiUrl } from "@/lib/apiUrl";
import { getAccessToken } from "@/state/tokenProvider"; // 👈 respetado

/** Base URL segura (normalizada) */
const BASE_URL = safeNormalizeBase(apiBase());

/** Respeta cookies httpOnly (refresh) si tu backend las usa */
const WITH_CREDS = true;

/** Timeout “realista” (Firefox suele cortar antes con timeouts muy bajos) */
const DEFAULT_TIMEOUT_MS = 15000;

/**
 * Crea el cliente principal
 * - baseURL centralizada (no duplica /api)
 * - withCredentials activado (cookies httpOnly)
 */
const axiosClient = axios.create({
    baseURL: BASE_URL,
    timeout: DEFAULT_TIMEOUT_MS,
    withCredentials: WITH_CREDS,
});

// Aceptar JSON por defecto + cabecera útil para CORS/CSRF simples
axiosClient.defaults.headers.common.Accept = "application/json";
axiosClient.defaults.headers.common["X-Requested-With"] = "XMLHttpRequest";

/* ======================================================================
 * REFRESH CON COLA (tu lógica avanzada: la conservamos y pulimos bordes)
 * ==================================================================== */
let isRefreshing = false;
/** @type {Array<{resolve:(t:string|null)=>void, reject:(err:any)=>void}>} */
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(({ resolve, reject }) =>
        error ? reject(error) : resolve(token)
    );
    failedQueue = [];
};

/* ======================================================================
 * REQUEST INTERCEPTOR
 * - Inyecta Authorization si hay token (store → localStorage)
 * - Mantiene Content-Type cuando no sea FormData
 * - Evita duplicar /api si llegan URLs absolutas
 * ==================================================================== */
axiosClient.interceptors.request.use(
    (config) => {
        // Evitar doble "/api": si la URL ya es absoluta, no toques baseURL
        // (Axios respeta la url absoluta y omite baseURL, pero lo dejamos explícito)
        if (isAbsoluteUrl(config.url)) {
            // no-op: axios ya ignora baseURL para urls absolutas
        }

        // Header Authorization (si no viene explícito)
        try {
            if (!config.headers?.Authorization) {
                // 1) Token desde store (Zustand/Redux) si existe
                let token = safeGetTokenFromStore();

                // 2) Fallback a localStorage con tu clave actual
                if (!token) {
                    token = localStorage.getItem(STORAGE_KEYS.accessToken);
                }

                if (token) {
                    config.headers = config.headers || {};
                    config.headers.Authorization = `Bearer ${token}`;
                }
            }
        } catch {
            // store/localStorage no disponible; seguimos sin romper
        }

        // Asegura Content-Type si mandamos JSON plano (no tocar FormData)
        if (
            config.data &&
            typeof FormData !== "undefined" &&
            !(config.data instanceof FormData)
        ) {
            config.headers = config.headers || {};
            if (!config.headers["Content-Type"]) {
                config.headers["Content-Type"] = "application/json";
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

/* ======================================================================
 * RESPONSE INTERCEPTOR
 * - 401/403 → intenta /auth/refresh (sin bucles)
 * - Cola de solicitudes en refresh
 * - Normaliza errores 502 de Nginx (Firefox los muestra mucho)
 * ==================================================================== */
axiosClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        // Si no hay response (network/CORS duro/timeout)
        if (!error?.response) {
            return Promise.reject(normalizeNetworkError(error));
        }

        const { config: originalRequest, response } = error;

        // Construye URL absoluta del refresh para comparar
        const refreshAbsolute = apiUrl("/auth/refresh");

        // Detecta si la request fallida es el propio refresh
        const originalAbs =
            ((originalRequest?.baseURL || "").replace(/\/$/, "")) +
            (originalRequest?.url || "");
        const isAuthRefreshCall =
            originalRequest?.url?.includes("/auth/refresh") ||
            stripSlash(originalAbs) === stripSlash(refreshAbsolute);

        // ¿Aplicamos refresh?
        const shouldTryRefresh =
            (response.status === 401 || response.status === 403) &&
            !originalRequest?._retry &&
            !isAuthRefreshCall;

        if (!shouldTryRefresh) {
            // Mejora: si es 502 por proxy, añade hint en el error para debugging
            if (response.status === 502) {
                error.message =
                    error.message ||
                    "Bad Gateway (502). Verifica el upstream /api en Nginx o el backend.";
            }
            return Promise.reject(error);
        }

        originalRequest._retry = true;

        // Si ya hay un refresh en progreso, encolamos esta solicitud
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then((token) => {
                    originalRequest.headers = originalRequest.headers || {};
                    if (token) originalRequest.headers.Authorization = `Bearer ${token}`;
                    return axiosClient(originalRequest);
                })
                .catch((err) => Promise.reject(err));
        }

        isRefreshing = true;

        try {
            // Hacemos el refresh con axios "plano" (no axiosClient) para evitar bucles
            const res = await axios.post(
                refreshAbsolute,
                {},
                { withCredentials: WITH_CREDS, timeout: DEFAULT_TIMEOUT_MS }
            );

            const newToken = res?.data?.access_token || res?.data?.token || null;
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

/* ======================================================================
 * Helpers públicos de token (respetando tu API)
 * ==================================================================== */

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

/** Exponer el cliente por si necesitas “inyectarlo” en tests/otros módulos */
export function getHttpClient() {
    return axiosClient;
}

/* ======================================================================
 * Health-checks opcionales (no afectan tu flujo actual)
 * ==================================================================== */

/**
 * Health del API:
 * - Intenta /health
 * - Si 404/405, prueba "/" o BASE_URL
 * Nunca lanza: devuelve { ok, status, data|error, url }.
 */
export async function healthCheckApi({ signal } = {}) {
    const candidates = [apiUrl("/health"), apiUrl("/"), BASE_URL];

    for (const url of candidates) {
        try {
            const res = await axios.get(url, {
                withCredentials: WITH_CREDS,
                timeout: 8000,
                signal,
            });
            if (res.status >= 200 && res.status < 300) {
                return { ok: true, status: res.status, data: res.data, url };
            }
        } catch {
            // siguiente candidato
        }
    }
    return {
        ok: false,
        status: 0,
        error: "API health-check falló",
        url: candidates[candidates.length - 1],
    };
}

/**
 * Health del Chat:
 * - TRANSPORT=rest → prueba VITE_CHAT_REST_URL y variantes /health
 * - WS/Rasa REST → prueba {rasaBase}/version
 * Devuelve { ok, status, data|error, url }. NO lanza.
 */
export async function healthCheckChat({ signal } = {}) {
    const TRANSPORT = (import.meta.env.VITE_CHAT_TRANSPORT || "rest").toLowerCase();
    const REST = (import.meta.env.VITE_CHAT_REST_URL || "").trim();
    const RASA = (import.meta.env.VITE_RASA_REST_URL || "").trim();

    async function tryList(urls) {
        for (const url of urls) {
            if (!url) continue;
            try {
                const res = await axios.get(url, { timeout: 8000, signal });
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
        const baseRest = REST || apiUrl("/chat");
        const candidates = [
            baseRest, // GET directo (si responde 200)
            stripSlash(baseRest) + "/health",
            apiUrl("/chat/health"),
            apiUrl("/health"),
            BASE_URL,
        ];
        return tryList(candidates);
    }

    // TRANSPORT === "ws" o Rasa REST directo
    const rasaWebhook = RASA || ""; // p.ej. http://localhost:5005/webhooks/rest/webhook
    const rasaBase = rasaWebhook.replace(/\/webhooks\/rest\/webhook\/?$/, "");
    const candidates = [rasaBase ? stripSlash(rasaBase) + "/version" : "", rasaBase];
    return tryList(candidates);
}

export default axiosClient;

/* ======================================================================
 * Utils internos
 * ==================================================================== */

function isAbsoluteUrl(url) {
    return /^https?:\/\//i.test(url || "");
}

function stripSlash(s) {
    return String(s || "").replace(/\/+$/, "");
}

function safeNormalizeBase(b) {
    // Normaliza: evita duplicar barras y garantiza prefijo /api si tu apiBase() lo trae
    const s = String(b || "").trim();
    if (!s) return "/api";
    // Elimina barras repetidas al final
    const clean = s.replace(/\/+$/, "");
    return clean || "/api";
}

function safeGetTokenFromStore() {
    try {
        const t = getAccessToken?.();
        return t || null;
    } catch {
        return null;
    }
}

function normalizeNetworkError(err) {
    // Mensaje más claro cuando Firefox o proxies devuelven net::ERR_* sin response
    const e = err || new Error("Network error");
    if (!e.message || e.message === "Network Error") {
        e.message =
            "No se pudo conectar con la API (Network/CORS/timeout). Revisa Nginx / CORS / proxy.";
    }
    return e;
}
