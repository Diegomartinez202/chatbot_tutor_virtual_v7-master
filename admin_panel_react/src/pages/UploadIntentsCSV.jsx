// src/components/UploadIntentsCSV.jsx
import { useState } from "react";
import axiosClient from "@/services/axiosClient";
import { Upload, Loader2, FileText, CheckCircle, XCircle } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

const UploadIntentsCSV = () => {
    const [file, setFile] = useState(null);
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const [isError, setIsError] = useState(false);

    const handleUpload = async () => {
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            setLoading(true);
            setMessage("");
            setIsError(false);

            const response = await axiosClient.post("/admin/intents/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            setMessage(response.data?.message || "Archivo CSV cargado correctamente");
            setIsError(false);
        } catch (error) {
            setMessage(error.response?.data?.detail || "Error al subir el archivo");
            setIsError(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6">
            {/* Título con icono + tooltip */}
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Cargar intents desde un archivo CSV" side="top">
                    <FileText className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h2 className="text-2xl font-semibold">Cargar Intents desde CSV</h2>
            </div>

            <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="mb-4"
            />
            <br />

            <IconTooltip label="Subir CSV a /admin/intents/upload" side="top">
                <button
                    onClick={handleUpload}
                    disabled={loading || !file}
                    className="bg-blue-600 text-white px-4 py-2 rounded inline-flex items-center gap-2 disabled:opacity-60"
                    type="button"
                    aria-label="Subir CSV de intents"
                >
                    {loading ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Cargando...
                        </>
                    ) : (
                        <>
                            <Upload className="w-4 h-4" />
                            Subir CSV
                        </>
                    )}
                </button>
            </IconTooltip>

            {message && (
                <div
                    className={[
                        "mt-4 p-2 rounded border inline-flex items-center gap-2",
                        isError
                            ? "text-red-700 bg-red-100 border-red-300"
                            : "text-green-700 bg-green-100 border-green-300",
                    ].join(" ")}
                    role="status"
                >
                    {isError ? (
                        <XCircle className="w-4 h-4" />
                    ) : (
                        <CheckCircle className="w-4 h-4" />
                    )}
                    <span>{message}</span>
                </div>
            )}
        </div>
    );
};

export default UploadIntentsCSV;