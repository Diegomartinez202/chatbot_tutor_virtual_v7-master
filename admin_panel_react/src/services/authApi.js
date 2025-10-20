import axiosClient from "./axiosClient";
import { setToken, clearToken, setRefreshToken } from "./tokenStorage";

/**
 * Endpoints prioritarios (mantiene compat y agrega panel admin).
 * - Se prioriza /api/admin/* para el panel administrativo (fallback /admin/*).
 * - Para auth "general" se mantienen /auth/* y sus alternativas.
 */
const PATHS = {
    login: ["/auth/login", "/login"],
    me: ["/auth/me", "/me"],
    refresh: [
        { method: "GET", url: "/auth/refresh" },
        { method: "POST", url: "/auth/refresh" },
        { method: "POST", url: "/auth/token/refresh" },
    ],
    logout: ["/auth/logout", "/logout"],

    // Admin panel
    admin: {
        register: ["/api/admin/register", "/admin/register"],
        login: ["/api/admin/login", "/admin/login"],
        me: ["/api/admin/me", "/admin/me"],
    },

    // Forgot password
    forgot: ["/auth/forgot-password", "/forgot-password"],
};

function pickFirst(arr) {
    return Array.isArray(arr) ? arr[0] : arr;
}

// ──────────────────────────────────────────────
// Token helpers
// ──────────────────────────────────────────────
export function setAuthToken(token) {
    if (!token) return;
    setToken(token);
    axiosClient.defaults.headers.common.Authorization = `Bearer ${token}`;
}

export function clearAuthToken() {
    clearToken();
    delete axiosClient.defaults.headers.common.Authorization;
}

// ──────────────────────────────────────────────
/** Auth API (general) */
// ──────────────────────────────────────────────
export async function login({ email, password }) {
    const url = pickFirst(PATHS.login);
    const { data } = await axiosClient.post(url, { email, password });

    const token = data?.access_token || data?.token || data?.jwt || null;
    const refresh = data?.refresh_token || null;

    if (token) setAuthToken(token);
    if (refresh) setRefreshToken(refresh);

    return { token, refresh_token: refresh, raw: data };
}

export async function loginWithToken(token) {
    setAuthToken(token);
    return { ok: true };
}

export async function me() {
    for (const u of PATHS.me) {
        try {
            const { data } = await axiosClient.get(u);
            return data;
        } catch {}
    }
    throw new Error("No se pudo obtener el perfil.");
}

export async function refresh(refreshTokenMaybe) {
    try {
        const { data } = await axiosClient.get(PATHS.refresh[0].url);
        const newTk = data?.access_token || data?.token || null;
        if (newTk) {
            setAuthToken(newTk);
            return { token: newTk, raw: data };
        }
    } catch {}

    const candidates = PATHS.refresh.slice(1);
    for (const cand of candidates) {
        try {
            const body = refreshTokenMaybe ? { refresh_token: refreshTokenMaybe } : {};
            const { data } = await axiosClient.post(cand.url, body);
            const newTk = data?.access_token || data?.token || null;
            const newRefresh = data?.refresh_token || null;

            if (newTk) {
                setAuthToken(newTk);
                if (newRefresh) setRefreshToken(newRefresh);
                return { token: newTk, raw: data };
            }
        } catch {}
    }

    clearAuthToken();
    throw new Error("Refresh inválido");
}

export async function logout() {
    try {
        const url = pickFirst(PATHS.logout);
        await axiosClient.post(url);
    } catch {}
    clearAuthToken();
    return { ok: true };
}

// ──────────────────────────────────────────────
/** Forgot password */
// ──────────────────────────────────────────────
export async function forgotPassword({ email }) {
    const url = pickFirst(PATHS.forgot);
    const { data } = await axiosClient.post(url, { email });
    return data;
}

// ──────────────────────────────────────────────
/** Admin panel (prioriza /api/admin/*) */
// ──────────────────────────────────────────────
export async function registerAdmin({
    name,
    email,
    password,
    accept_terms = true,
}) {
    const url = pickFirst(PATHS.admin.register);
    const { data } = await axiosClient.post(url, {
        name,
        email,
        password,
        accept_terms,
    });
    return {
        ok: data?.ok === true || !!data?.id,
        id: data?.id,
        message: data?.message || "ok",
    };
}

export async function loginAdmin({ email, password }) {
    const url = pickFirst(PATHS.admin.login);
    const { data } = await axiosClient.post(url, { email, password });
    const token = data?.access_token ?? data?.token ?? null;
    if (token) setAuthToken(token);
    return { token, raw: data };
}

export async function adminMe() {
    const url = pickFirst(PATHS.admin.me);
    const { data } = await axiosClient.get(url);
    return data;
}

// Aliases por compatibilidad con tu código actual
export const apiLogin = login;
export const apiMe = me;

// 🔹 Alias agregado para que RegisterPage.jsx no rompa
export const register = registerAdmin;
