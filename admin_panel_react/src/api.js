// admin_panel_react/src/api.js
import axios from "axios";

// =========================
// Config baseURL por entorno
// =========================
// Prioriza variable de entorno; cae a prod/dev según host
const DEFAULT_API = (() => {
    // Si sirves el backend en el mismo dominio, a veces conviene relativo: "/api"
    // Cambia esto a lo que realmente uses en despliegue:
    if (import.meta?.env?.VITE_API_BASE) return import.meta.env.VITE_API_BASE;
    if (window.location.hostname === "localhost") return "http://localhost:5000/api";
    // ejemplo prod:
    return "https://api.zajuna.com/api";
})();

const api = axios.create({
    baseURL: DEFAULT_API,
    headers: { "Content-Type": "application/json" },
    withCredentials: true, // ⬅️ si usas cookies cross-site además del Bearer
});

// Inyecta Bearer automático desde localStorage
api.interceptors.request.use((config) => {
    try {
        const t = localStorage.getItem("accessToken");
        if (t) config.headers.Authorization = `Bearer ${t}`;
    } catch { }
    return config;
});

// Manejo de 401 básico
api.interceptors.response.use(
    (res) => res,
    (err) => {
        const status = err?.response?.status;
        if (status === 401) {
            // Opcional: limpia token y redirige a login
            // localStorage.removeItem("accessToken");
            // window.location.href = "/login";
        }
        return Promise.reject(err);
    }
);

// ----------------------
// Funciones API (igual que tu TS, sin tipos)
// ----------------------
export const fetchIntentsPaged = async (page, limit) => {
    const { data } = await api.get(`/intents?page=${page}&limit=${limit}`);
    return data;
};

export const fetchIntentById = async (id) => {
    const { data } = await api.get(`/intents/${id}`);
    return data;
};

export const createIntent = async (payload) => {
    const { data } = await api.post("/intents", payload);
    return data;
};

export const updateIntent = async (id, payload) => {
    const { data } = await api.put(`/intents/${id}`, payload);
    return data;
};

export const deleteIntent = async (id) => {
    const { data } = await api.delete(`/intents/${id}`);
    return data;
};

export default api;
