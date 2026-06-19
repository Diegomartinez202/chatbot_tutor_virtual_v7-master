// src/components/IntentEditor.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Save, X, Trash2, Loader2, Info } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import { Button } from "@/components/ui/button";
import toast from "react-hot-toast";

function toArrayFromMultiline(val = "") {
    return String(val)
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
}
function toMultilineFromArray(arr) {
    if (!Array.isArray(arr)) return "";
    return arr.join("\n");
}

export default function IntentEditor({
    mode = "create", // "create" | "edit"
    initialData = null, // { intent, examples:[], responses:[] }
    loading = false,
    onSubmit, // (payload) => Promise|void
    onDelete, // () => Promise|void
    onCancel, // () => void
}) {
    const isEdit = mode === "edit";

    // estado de formulario
    const [intent, setIntent] = useState("");
    const [examples, setExamples] = useState("");
    const [responses, setResponses] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [deleting, setDeleting] = useState(false);

    // precargar
    useEffect(() => {
        if (!initialData) return;
        setIntent(initialData.intent || "");
        setExamples(toMultilineFromArray(initialData.examples || initialData.examples_list || []));
        setResponses(toMultilineFromArray(initialData.responses || initialData.responses_list || []));
    }, [initialData]);

    const canSubmit = useMemo(() => {
        return (
            intent.trim().length > 0 &&
            toArrayFromMultiline(examples).length > 0 &&
            toArrayFromMultiline(responses).length > 0
        );
    }, [intent, examples, responses]);

    const handleSubmit = async (e) => {
        e?.preventDefault?.();
        if (!onSubmit) return;

        const payload = {
            intent: intent.trim(),
            examples: toArrayFromMultiline(examples),
            responses: toArrayFromMultiline(responses),
        };

        try {
            setSubmitting(true);
            await Promise.resolve(onSubmit(payload));
            toast.success(isEdit ? "Intent actualizado" : "Intent creado");
        } catch (err) {
            console.error(err);
            toast.error("No se pudo guardar el intent");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!onDelete) return;
        if (!confirm("¿Eliminar este intent? Esta acción no se puede deshacer.")) return;
        try {
            setDeleting(true);
            await Promise.resolve(onDelete());
            toast.success("Intent eliminado");
        } catch (err) {
            console.error(err);
            toast.error("No se pudo eliminar el intent");
        } finally {
            setDeleting(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4 bg-white p-4 rounded-md border">
            <div className="flex items-center justify-between">
                <h1 className="text-lg font-semibold">
                    {isEdit ? "Editar intent" : "Crear intent"}
                </h1>
                <div className="flex items-center gap-2">
                    <IconTooltip label="Consejo: usa frases reales, variadas y cortas para 'Ejemplos'">
                        <Info className="w-4 h-4 text-gray-500" aria-hidden="true" />
                    </IconTooltip>
                </div>
            </div>

            {/* Intent */}
            <div>
                <label className="block text-sm font-medium mb-1">
                    Nombre del intent
                </label>
                <input
                    type="text"
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    placeholder="p.ej. saludo"
                    value={intent}
                    onChange={(e) => setIntent(e.target.value)}
                    disabled={isEdit || loading || submitting}
                    aria-describedby={isEdit ? "help-intent" : undefined}
                />
                {isEdit && (
                    <p id="help-intent" className="text-xs text-gray-500 mt-1">
                        El nombre del intent no puede cambiarse (clave primaria).
                    </p>
                )}
            </div>

            {/* Examples */}
            <div>
                <div className="flex items-center gap-2">
                    <label className="block text-sm font-medium">Ejemplos (uno por línea)</label>
                    <IconTooltip label="Cada línea es una frase de entrenamiento">
                        <Info className="w-4 h-4 text-gray-500" aria-hidden="true" />
                    </IconTooltip>
                </div>
                <textarea
                    className="w-full border rounded-md px-3 py-2 text-sm min-h-[120px]"
                    placeholder={"hola\nbuenas\nqué tal"}
                    value={examples}
                    onChange={(e) => setExamples(e.target.value)}
                    disabled={loading || submitting}
                />
            </div>

            {/* Responses */}
            <div>
                <div className="flex items-center gap-2">
                    <label className="block text-sm font-medium">Respuestas (una por línea)</label>
                    <IconTooltip label="Puedes definir varias, el bot elegirá">
                        <Info className="w-4 h-4 text-gray-500" aria-hidden="true" />
                    </IconTooltip>
                </div>
                <textarea
                    className="w-full border rounded-md px-3 py-2 text-sm min-h-[120px]"
                    placeholder={"¡Hola! ¿En qué puedo ayudarte?\nHola, dime en qué te ayudo"}
                    value={responses}
                    onChange={(e) => setResponses(e.target.value)}
                    disabled={loading || submitting}
                />
            </div>

            {/* Acciones */}
            <div className="flex flex-wrap items-center gap-2 justify-end pt-2">
                <IconTooltip label="Cancelar y volver">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={onCancel}
                        disabled={loading || submitting}
                        aria-label="Cancelar"
                    >
                        <X className="w-4 h-4 mr-2" />
                        Cancelar
                    </Button>
                </IconTooltip>

                {isEdit && (
                    <IconTooltip label="Eliminar intent">
                        <Button
                            type="button"
                            variant="destructive"
                            onClick={handleDelete}
                            disabled={loading || submitting || deleting}
                            aria-label="Eliminar intent"
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
                )}

                <IconTooltip label={isEdit ? "Guardar cambios" : "Crear intent"}>
                    <Button
                        type="submit"
                        disabled={!canSubmit || loading || submitting}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white"
                        aria-label={isEdit ? "Guardar cambios" : "Crear intent"}
                    >
                        {submitting ? (
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                            <Save className="w-4 h-4 mr-2" />
                        )}
                        {isEdit ? "Guardar" : "Crear"}
                    </Button>
                </IconTooltip>
            </div>
        </form>
    );
}