// src/pages/IntentDetail.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getIntentById, deleteIntent } from "@/services/api";
import {
    ArrowLeft,
    Pencil,
    Trash2,
    Loader2,
    AlertCircle,
    ClipboardList,
} from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import { Button } from "@/components/ui/button";
import toast from "react-hot-toast";

export default function IntentDetail() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [intent, setIntent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        let active = true;
        (async () => {
            try {
                setLoading(true);
                const data = await getIntentById(id);
                if (!active) return;
                setIntent({
                    intent: data?.intent ?? id,
                    examples: data?.examples ?? data?.examples_list ?? [],
                    responses: data?.responses ?? data?.responses_list ?? [],
                });
            } catch (e) {
                console.error(e);
                toast.error("No se pudo cargar el intent");
            } finally {
                if (active) setLoading(false);
            }
        })();
        return () => {
            active = false;
        };
    }, [id]);

    const handleDelete = async () => {
        if (!confirm("¿Eliminar este intent?")) return;
        try {
            setDeleting(true);
            await deleteIntent(id);
            toast.success("Intent eliminado");
            navigate("/intents/list");
        } catch (e) {
            console.error(e);
            toast.error("No se pudo eliminar el intent");
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="p-4 space-y-4">
            {/* header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <ClipboardList className="w-5 h-5 text-gray-700" />
                    <h2 className="text-xl font-semibold">Detalle del intent</h2>
                </div>

                <div className="flex items-center gap-2">
                    <IconTooltip label="Volver a la lista">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => navigate("/intents/list")}
                        >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Volver
                        </Button>
                    </IconTooltip>

                    <IconTooltip label="Editar intent">
                        <Button
                            type="button"
                            onClick={() => navigate(`/intents/${encodeURIComponent(id)}/edit`)}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white"
                        >
                            <Pencil className="w-4 h-4 mr-2" />
                            Editar
                        </Button>
                    </IconTooltip>

                    <IconTooltip label="Eliminar intent">
                        <Button
                            type="button"
                            onClick={handleDelete}
                            disabled={deleting}
                            className="bg-red-600 hover:bg-red-700 text-white"
                        >
                            {deleting ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                                <Trash2 className="w-4 h-4 mr-2" />
                            )}
                            Eliminar
                        </Button>
                    </IconTooltip>
                </div>
            </div>

            {/* contenido */}
            {loading ? (
                <div className="flex items-center gap-2 text-gray-600">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Cargando…
                </div>
            ) : !intent ? (
                <div className="flex items-center gap-2 text-red-600">
                    <AlertCircle className="w-4 h-4" />
                    No se encontró el intent.
                </div>
            ) : (
                <div className="rounded-md border bg-white p-4">
                    <div className="mb-4">
                        <div className="text-xs uppercase tracking-wide text-gray-500">Intent</div>
                        <div className="text-base font-semibold">{intent.intent}</div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <section>
                            <div className="text-sm font-medium mb-1">Ejemplos</div>
                            {intent.examples?.length ? (
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-800">
                                    {intent.examples.map((ex, i) => (
                                        <li key={i}>{ex}</li>
                                    ))}
                                </ul>
                            ) : (
                                <div className="text-gray-400 text-sm">—</div>
                            )}
                        </section>

                        <section>
                            <div className="text-sm font-medium mb-1">Respuestas</div>
                            {intent.responses?.length ? (
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-800">
                                    {intent.responses.map((res, i) => (
                                        <li key={i}>{res}</li>
                                    ))}
                                </ul>
                            ) : (
                                <div className="text-gray-400 text-sm">—</div>
                            )}
                        </section>
                    </div>
                </div>
            )}
        </div>
    );
}