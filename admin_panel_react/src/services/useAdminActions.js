// src/services/useAdminActions.js
import { useMutation } from "@tanstack/react-query";
import axiosClient from "./axiosClient";
import toast from "react-hot-toast";

// === Helpers internos ===
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

// === Mutations base ===
// 👉 Compat: sin argumentos funciona como antes (LOCAL).
//    Si quieres CI: trainMutation.mutate({ mode: "ci", branch: "main" })
const trainBot = (payload) => axiosClient.post("/admin/train", payload || {});
const uploadIntents = () => axiosClient.post("/admin/upload");
const restartServerReq = () => axiosClient.post("/admin/restart");

// Export logs CSV (rango fechas) desde /admin/exportaciones
const exportLogsCsv = ({ desde, hasta }) =>
    axiosClient.get("/admin/exportaciones", {
        responseType: "blob",
        params: { desde, hasta },
    });

// Opcional: export tests
const exportTestsCsv = () =>
    axiosClient.get("/admin/exportaciones/tests", { responseType: "blob" });

export function useAdminActions() {
    const trainMutation = useMutation({
        mutationFn: trainBot,
        onSuccess: (res) => {
            const mode = res?.data?.mode || "local";
            toast.success(
                mode === "ci" ? "🚀 CI/CD disparado (entrenamiento/deploy)" : "🤖 Entrenamiento iniciado (local)"
            );
        },
        onError: (e) => toast.error(e?.response?.data?.detail || "Error al entrenar"),
    });

    const uploadMutation = useMutation({
        mutationFn: uploadIntents,
        onSuccess: () => toast.success("📤 Intents enviados"),
        onError: (e) => toast.error(e?.response?.data?.detail || "Error al subir intents"),
    });

    const restartMutation = useMutation({
        mutationFn: restartServerReq,
        onSuccess: () => toast.success("🔁 Reinicio solicitado"),
        onError: (e) => toast.error(e?.response?.data?.detail || "Error al reiniciar"),
    });

    const exportMutation = useMutation({
        mutationFn: async ({ desde, hasta }) => {
            const res = await exportLogsCsv({ desde, hasta });

            const contentType = res.headers?.["content-type"] || "";
            if (contentType.includes("application/json")) {
                const text = await res.data.text?.();
                try {
                    const json = JSON.parse(text);
                    throw new Error(json?.detail || json?.message || "Error al exportar");
                } catch {
                    throw new Error("Error al exportar");
                }
            }

            const ts = new Date().toISOString().split("T")[0];
            const range = (desde ? `_${desde}` : "") + (hasta ? `_${hasta}` : "");
            const fallbackName = `exportacion_logs${range || `_${ts}`}.csv`;

            const filename = getFilenameFromCD(res.headers, fallbackName);
            const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
            downloadBlob(blob, filename, /* addBom */ true);
        },
        onSuccess: () => toast.success("✅ Exportación CSV completada"),
        onError: (err) => toast.error(err?.message || "❌ Error al exportar resultados"),
    });

    const exportTestsMutation = useMutation({
        mutationFn: async () => {
            const res = await exportTestsCsv();
            const filename = getFilenameFromCD(res.headers, "resultados_test.csv");
            const blob = new Blob([res.data], { type: "text/csv;charset=utf-8" });
            downloadBlob(blob, filename, /* addBom */ true);
        },
        onSuccess: () => toast.success("✅ Export de tests listo"),
        onError: () => toast.error("❌ Error al exportar resultados de tests"),
    });

    return {
        trainMutation,
        uploadMutation,
        restartMutation,
        exportMutation,
        exportTestsMutation, // úsalo si lo necesitas
    };
}