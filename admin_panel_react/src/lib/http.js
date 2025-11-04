// src/lib/http.js
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export const http = axios.create({
    baseURL: API_BASE.replace(/\/$/, ""),
    withCredentials: true, // <- permite cookies/sesiones cross-site si CORS lo permite
    timeout: 15000,
});

// Lee token desde localStorage (o tu store)
function getToken() {
    try {
        return (
            localStorage.getItem("access_token") ||
            localStorage.getItem("zajuna_token") ||
            localStorage.getItem("app:token") ||
            null
        );
    } catch {
        return null;
    }
}

// Request: agrega Authorization si hay token
http.interceptors.request.use((config) => {
    const token = getToken();
    if (token && !config.headers?.Authorization) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response: manejo de 401 centralizado (opcional)
http.interceptors.response.use(
    (rsp) => rsp,
    (err) => {
        const status = err?.response?.status;
        if (status === 401) {
            // Opcional: limpiar token y redirigir
            try {
                localStorage.removeItem("access_token");
                localStorage.removeItem("zajuna_token");
            } catch { }
            // Ejemplo: redirigir a login si NO estás en modo invitado
            if (window.location.pathname !== "/login") {
                // window.location.href = "/login";
            }
        }
        return Promise.reject(err);
    }
);
