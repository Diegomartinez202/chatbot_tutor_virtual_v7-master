// src/services/api.js
import axiosClient from "./axiosClient";

/* =========================
   Utils descarga (CSV/Blob)
   ========================= */
function getFilenameFromCD(headers, fallback) {
    const cd = headers?.["content-disposition"];
    if (!cd) return fallback;
    const m = /filename\*=UTF-8''([^;]+)|filename="?([^"]+)"?/i.exec(cd);
    try {
        const raw = decodeURIComponent(m?.[1] || m?.[2] || "");
        return raw || fallback;
    } catch {
        return fallback;
    }
}

function downloadBlob(blob, filename, addBom = false) {
    const finalBlob =
        addBom && blob.type?.startsWith("text/csv")
            ? new Blob(["\uFEFF", blob], { type: blob.type })
            : blob;

    const url = window.URL.createObjectURL(finalBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

/* =========================
   📁 INTENTS
   ========================= */

// Lista de intents
export const fetchIntents = () =>
    axiosClient.get("/admin/intents").then((r) => r.data);

// Alias retro
export const getIntents = fetchIntents;

// Filtro por querystring
export const fetchIntentsByFilters = ({ intent, example, response }) => {
    const query = new URLSearchParams();
    if (intent) query.append("intent", intent);
    if (example) query.append("example", example);
    if (response) query.append("response", response);
    return axiosClient
        .get(`/admin/intents?${query.toString()}`)
        .then((r) => r.data);
};

// ✅ obtener un intent por id/nombre
export const getIntentById = (intentName) =>
    axiosClient
        .get(`/admin/intents/${encodeURIComponent(intentName)}`)
        .then((r) => r.data);

// ✅ crear/actualizar/eliminar
export const createIntent = (intentData) =>
    axiosClient.post("/admin/intents", intentData);

export const updateIntent = (intentName, intentData) =>
    axiosClient.put(`/admin/intents/${encodeURIComponent(intentName)}`, intentData);

export const deleteIntent = (intentName) =>
    axiosClient.delete(`/admin/intents/${encodeURIComponent(intentName)}`);

// Compat (alias legacy)
export const addIntent = createIntent;
export const removeIntent = deleteIntent;

// Upload JSON/CSV y export
export const uploadIntentJSON = (data) =>
    axiosClient.post("/admin/intents/upload-json", data);

export const uploadIntentsCSV = (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return axiosClient.post("/admin/intents/upload-csv", formData, {
        headers: { "Content-Type": "multipart/form-data" },
    });
};

export const exportIntentsCSV = async () => {
    const res = await axiosClient.get("/admin/intents/export", {
        responseType: "blob",
    });
    const filename = getFilenameFromCD(res.headers, "intents.csv");
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, filename, /* addBom */ true);
};

/* =========================
   📁 ENTRENAMIENTO
   ========================= */
export const trainBot = () => axiosClient.post("/admin/train");

/* =========================
   📁 USUARIOS
   ========================= */
export const fetchUsers = () =>
    axiosClient.get("/admin/users").then((r) => r.data);

// Alias retro
export const getUsers = fetchUsers;

export const deleteUser = (userId) =>
    axiosClient.delete(`/admin/users/${userId}`);

export const updateUser = (userId, userData) =>
    axiosClient.put(`/admin/users/${userId}`, userData);

export const createUser = (userData) =>
    axiosClient.post("/admin/users", userData);

export const exportUsersCSV = async () => {
    const res = await axiosClient.get("/admin/users/export", {
        responseType: "blob",
    });
    const filename = getFilenameFromCD(
        res.headers,
        `usuarios_exportados_${new Date().toISOString().slice(0, 10)}.csv`
    );
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, filename, /* addBom */ true);
};

/* =========================
   📁 AUTENTICACIÓN
   ========================= */
export const login = (credentials) =>
    axiosClient.post("/auth/login", credentials);
export const refreshToken = () => axiosClient.post("/auth/refresh");
export const register = (userData) => axiosClient.post("/auth/register", userData);

/* =========================
   📁 DIAGNÓSTICO / TEST
   ========================= */
export const ping = () => axiosClient.get("/ping");
export const testIntents = () => axiosClient.get("/admin/intents/test");

/* =========================
   📁 LOGS
   ========================= */
export const getLogsList = () =>
    axiosClient.get("/admin/logs").then((res) => res.data);

export const downloadLogFile = async (filename) => {
    const res = await axiosClient.get(
        `/admin/logs/${encodeURIComponent(filename)}`,
        { responseType: "blob" }
    );
    const blob = new Blob([res.data], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, filename || "log.txt", /* addBom */ false);
};

export const exportLogsCSV = async () => {
    const res = await axiosClient.get("/admin/logs/export", {
        responseType: "blob",
    });
    const filename = getFilenameFromCD(res.headers, "logs.csv");
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, filename, /* addBom */ true);
};

export const getSystemLogs = async () => {
    const res = await axiosClient.get("/admin/logs-file", {
        responseType: "text",
    });
    return res.data;
};

/* =========================
   📊 ESTADÍSTICAS
   ========================= */
// Intenta /admin/stats y si no existe, cae a /api/stats (compat)
export async function getStats(params = {}) {
    const qs = new URLSearchParams(params).toString();
    try {
        const res = await axiosClient.get(`/admin/stats${qs ? "?" + qs : ""}`);
        return res.data;
    } catch (e) {
        if (e?.response?.status === 404) {
            const res2 = await axiosClient.get(`/api/stats${qs ? "?" + qs : ""}`);
            return res2.data;
        }
        throw e;
    }
}

/* =========================
   📤 EXPORTACIONES CSV
   ========================= */
export const exportarCSV = async (desde, hasta) => {
    const params = {};
    const asStr = (v) => (v instanceof Date ? v.toISOString().slice(0, 10) : v || undefined);
    const d = asStr(desde);
    const h = asStr(hasta);
    if (d) params.desde = d;
    if (h) params.hasta = h;

    const res = await axiosClient.get("/admin/exportaciones", {
        params,
        responseType: "blob",
    });
    const nameRange =
        (d ? `_${d}` : "") + (h ? `_${h}` : "");
    const fallbackName =
        `exportacion_logs${nameRange || `_${new Date().toISOString().slice(0, 10)}`}.csv`;
    const filename = getFilenameFromCD(res.headers, fallbackName);
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, filename, /* addBom */ true);
};

export const fetchHistorialExportaciones = ({ usuario, tipo } = {}) =>
    axiosClient
        .get("/admin/exportaciones/historial", { params: { usuario, tipo } })
        .then((res) => res.data);

export const exportTestResults = async () => {
    const res = await axiosClient.get("/admin/exportaciones/tests", {
        responseType: "blob",
    });
    const filename = getFilenameFromCD(res.headers, "resultados_test.csv");
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, filename, /* addBom */ true);
};

/* =========================
   🔁 UTILIDADES
   ========================= */
export const restartServer = () => axiosClient.post("/admin/restart");

// (alias opcional)
export { default as axios } from "@/services/axiosClient";

/* =========================
   ❌ INTENTOS FALLIDOS
   ========================= */
export const getTopFailedIntents = ({ desde, hasta, limit } = {}) =>
    axiosClient
        .get("/admin/intentos-fallidos/top", {
            params: { desde, hasta, limit },
        })
        .then((r) => r.data);

export const getFailedLogs = ({
    desde,
    hasta,
    intent,
    page,
    page_size,
} = {}) =>
    axiosClient
        .get("/admin/intentos-fallidos/logs", {
            params: { desde, hasta, intent, page, page_size },
        })
        .then((r) => r.data);

export const getFallbackLogs = () => getFailedLogs({ page: 1, page_size: 50 });

export const exportFailedIntentsCSV = async ({ desde, hasta, intent } = {}) => {
    const res = await axiosClient.get("/admin/intentos-fallidos/export", {
        params: { desde, hasta, intent },
        responseType: "blob",
    });
    const filename = getFilenameFromCD(
        res.headers,
        `intentos_fallidos_${new Date().toISOString().slice(0, 10)}.csv`
    );
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
    downloadBlob(blob, filename, /* addBom */ true);
};

/* =========================
   🔎 BÚSQUEDAS PAGINADAS
   ========================= */
// ⬇️ VERSIÓN LEGACY (con /admin/intents y filtros básicos)
export async function fetchIntentsPagedLegacy({
    intent,
    example,
    response,
    q,
    page = 1,
    page_size = 10,
    sort_by,
    sort_dir,
} = {}) {
    const params = new URLSearchParams();
    if (intent) params.append("intent", intent);
    if (example) params.append("example", example);
    if (response) params.append("response", response);
    if (q) params.append("q", q);
    if (page) params.append("page", String(page));
    if (page_size) params.append("page_size", String(page_size));
    if (sort_by) params.append("sort_by", sort_by);
    if (sort_dir) params.append("sort_dir", sort_dir);

    const res = await axiosClient.get(`/admin/intents?${params.toString()}`);
    const data = res.data;
    if (Array.isArray(data)) {
        return {
            items: data,
            total: data.length,
            page: Number(page) || 1,
            page_size: Number(page_size) || data.length || 10,
        };
    }
    return {
        items: data?.items ?? [],
        total: data?.total ?? 0,
        page: data?.page ?? Number(page) ?? 1,
        page_size: data?.page_size ?? Number(page_size) ?? 10,
    };
}

// ⬇️ VERSIÓN NUEVA (endpoint dedicado /admin/intents/paged)
export async function fetchIntentsPaged({
    page = 1,
    page_size = 10,
    q,
    intent,
    example,
    response,
    sort_by,   // "intent" | "example" | "response"
    sort_dir,  // "asc" | "desc"
} = {}) {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(page_size));
    if (q) params.set("q", q);
    if (intent) params.set("intent", intent);
    if (example) params.set("example", example);
    if (response) params.set("response", response);
    if (sort_by) params.set("sort_by", sort_by);
    if (sort_dir) params.set("sort_dir", sort_dir);

    const { data } = await axiosClient.get(`/admin/intents/paged?${params.toString()}`);
    return {
        items: data?.items ?? [],
        total: Number(data?.total ?? 0),
        page: Number(data?.page ?? page),
        page_size: Number(data?.page_size ?? page_size),
    };
}

/* =========================
   📦 DEFAULT EXPORT (comodidad)
   ========================= */
const api = {
    // intents
    fetchIntents,
    getIntents,
    fetchIntentsByFilters,
    getIntentById,
    createIntent,
    updateIntent,
    deleteIntent,
    addIntent,
    removeIntent,
    uploadIntentJSON,
    uploadIntentsCSV,
    exportIntentsCSV,

    // entrenamiento
    trainBot,

    // users
    fetchUsers,
    getUsers,
    deleteUser,
    updateUser,
    createUser,
    exportUsersCSV,

    // auth
    login,
    refreshToken,
    register,

    // diagnóstico
    ping,
    testIntents,

    // logs
    getLogsList,
    downloadLogFile,
    exportLogsCSV,
    getSystemLogs,

    // stats
    getStats,

    // exportaciones
    exportarCSV,
    fetchHistorialExportaciones,
    exportTestResults,

    // misc
    restartServer,

    // fallidos
    getTopFailedIntents,
    getFailedLogs,
    getFallbackLogs,

    // paginadas
    fetchIntentsPaged,
    fetchIntentsPagedLegacy,
};

export default api;