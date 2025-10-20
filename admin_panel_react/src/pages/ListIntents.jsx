import React, { useEffect, useState } from "react";
import { ClipboardList, AlertCircle } from "lucide-react";
import { getIntents } from "@/services/api";
import BackButton from "@/components/BackButton";
import RefreshButton from "@/components/RefreshButton";
import IconTooltip from "@/components/ui/IconTooltip";

export default function ListIntents() {
    const [intents, setIntents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadError, setLoadError] = useState("");

    const cargarIntents = async () => {
        setLoading(true);
        setLoadError("");
        try {
            const data = await getIntents();
            setIntents(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Error al cargar intents:", error);
            setLoadError("No se pudieron cargar los intents. Intenta nuevamente.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        cargarIntents();
    }, []);

    return (
        <div className="p-4">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                    <ClipboardList className="w-5 h-5 text-gray-700" aria-hidden="true" />
                    <h2 className="text-2xl font-bold">Lista de Intents</h2>
                    <IconTooltip label="Intents detectados por el bot (ejemplos y respuestas)">
                        <AlertCircle className="w-4 h-4 text-gray-500" aria-hidden="true" />
                    </IconTooltip>
                </div>

                <div className="flex gap-2">
                    <BackButton to="/intents" label="Volver a crear Intent" />
                    <RefreshButton
                        onClick={cargarIntents}
                        loading={loading}
                        label="Recargar"
                        tooltipLabel="Recargar lista"
                        variant="outline"
                    />
                </div>
            </div>

            {/* Estado de error */}
            {loadError && (
                <div className="mb-3 flex items-center gap-2 text-sm text-red-600">
                    <AlertCircle className="w-4 h-4" />
                    <span>{loadError}</span>
                </div>
            )}

            <div className="overflow-auto rounded-lg shadow">
                <table className="min-w-full divide-y divide-gray-200 bg-white">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Intent</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Ejemplos</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Respuestas</th>
                        </tr>
                    </thead>

                    <tbody className="divide-y divide-gray-200">
                        {/* Loading row */}
                        {loading && (
                            <tr>
                                <td colSpan={3} className="px-4 py-6 text-center text-gray-500">
                                    Cargando…
                                </td>
                            </tr>
                        )}

                        {!loading &&
                            intents.map((intent) => (
                                <tr key={intent.intent}>
                                    <td className="px-4 py-2 align-top font-semibold">{intent.intent}</td>
                                    <td className="px-4 py-2 align-top text-sm text-gray-700">
                                        {Array.isArray(intent.examples) && intent.examples.length > 0 ? (
                                            <ul className="list-disc list-inside space-y-1">
                                                {intent.examples.map((ex, idx) => (
                                                    <li key={idx}>{ex}</li>
                                                ))}
                                            </ul>
                                        ) : (
                                            <span className="text-gray-400">—</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-2 align-top text-sm text-gray-700">
                                        {Array.isArray(intent.responses) && intent.responses.length > 0 ? (
                                            <ul className="list-disc list-inside space-y-1">
                                                {intent.responses.map((res, idx) => (
                                                    <li key={idx}>{res}</li>
                                                ))}
                                            </ul>
                                        ) : (
                                            <span className="text-gray-400">—</span>
                                        )}
                                    </td>
                                </tr>
                            ))}

                        {!loading && intents.length === 0 && !loadError && (
                            <tr>
                                <td colSpan={3} className="px-4 py-6 text-center text-gray-500">
                                    No hay intents disponibles.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}