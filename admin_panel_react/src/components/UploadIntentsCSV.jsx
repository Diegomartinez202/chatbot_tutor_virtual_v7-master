// src/components/UploadIntentsCSV.jsx
import { useState, useRef } from "react";
import { uploadIntentJSON } from "@/services/api"; // Alias correcto
import { toast } from "react-hot-toast";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import { Upload, FileJson, Loader2, Info } from "lucide-react";

function UploadIntentsCSV() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const inputRef = useRef(null);

    const handleFileChange = (e) => {
        const selected = e.target.files?.[0];
        const isJson =
            selected &&
            (selected.type === "application/json" ||
                selected.name?.toLowerCase().endsWith(".json"));

        if (isJson) {
            setFile(selected);
        } else {
            setFile(null);
            toast.error("El archivo debe ser .json");
        }
    };

    const handleUpload = async () => {
        if (!file) {
            toast.error("Selecciona un archivo .json válido");
            return;
        }

        try {
            setLoading(true);
            const text = await file.text();
            const jsonData = JSON.parse(text);

            await uploadIntentJSON(jsonData);

            toast.success("Intent JSON subido correctamente");
            // Limpia selección tras éxito
            setFile(null);
            if (inputRef.current) inputRef.current.value = "";
        } catch (err) {
            console.error(err);
            toast.error("Error al subir el archivo JSON");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="border p-4 rounded bg-white shadow my-6">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <FileJson className="w-5 h-5 text-gray-700" aria-hidden="true" />
                    <h3 className="font-semibold">Subir intent desde archivo JSON</h3>
                    <IconTooltip label="Selecciona un archivo .json con tus intents para importarlos.">
                        <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                    </IconTooltip>
                </div>
            </div>

            <div className="flex flex-col gap-3">
                <input
                    ref={inputRef}
                    type="file"
                    accept=".json,application/json"
                    onChange={handleFileChange}
                    aria-label="Seleccionar archivo JSON de intents"
                    className="block w-full text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:bg-gray-50 file:hover:bg-gray-100 file:cursor-pointer"
                />

                {file && (
                    <div className="text-xs text-gray-600">
                        Archivo seleccionado: <span className="font-medium">{file.name}</span>
                    </div>
                )}

                <div>
                    <IconTooltip label={loading ? "Subiendo..." : "Subir archivo JSON"}>
                        <span>
                            <Button
                                onClick={handleUpload}
                                disabled={loading}
                                className="inline-flex items-center gap-2"
                                type="button"
                                aria-label="Subir y procesar archivo JSON de intents"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Cargando…
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-4 h-4" />
                                        Subir
                                    </>
                                )}
                            </Button>
                        </span>
                    </IconTooltip>
                </div>
            </div>
        </div>
    );
}

export default UploadIntentsCSV;

