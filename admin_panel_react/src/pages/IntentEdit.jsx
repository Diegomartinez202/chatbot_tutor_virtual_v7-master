// src/pages/IntentEdit.jsx
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
    getIntentById,
    createIntent,
    updateIntent,
    deleteIntent,
} from "@/services/api";
import { ArrowLeft, Edit3, PlusCircle, Loader2 } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import IntentEditor from "@/components/IntentEditor";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/button";

export default function IntentEdit() {
    const navigate = useNavigate();
    const { id } = useParams(); // si hay id → edición
    const isEdit = Boolean(id);

    const [initialData, setInitialData] = useState(null);
    const [loading, setLoading] = useState(isEdit);

    useEffect(() => {
        let active = true;
        const load = async () => {
            if (!isEdit) return;
            try {
                setLoading(true);
                const data = await getIntentById(id);
                if (!active) return;
                setInitialData({
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
        };
        load();
        return () => {
            active = false;
        };
    }, [id, isEdit]);

    const handleSubmit = async (payload) => {
        if (isEdit) {
            await updateIntent(id, payload);
            navigate("/intents/list");
        } else {
            await createIntent(payload);
            navigate("/intents/list");
        }
    };

    const handleDelete = async () => {
        await deleteIntent(id);
        navigate("/intents/list");
    };

    return (
        <div className="p-4 space-y-4">
            {/* header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {isEdit ? (
                        <Edit3 className="w-5 h-5 text-gray-700" />
                    ) : (
                        <PlusCircle className="w-5 h-5 text-gray-700" />
                    )}
                    <h2 className="text-xl font-semibold">
                        {isEdit ? `Editar: ${id}` : "Crear nuevo intent"}
                    </h2>
                </div>

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
            </div>

            {loading ? (
                <div className="flex items-center gap-2 text-gray-600">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Cargando…
                </div>
            ) : (
                <IntentEditor
                    mode={isEdit ? "edit" : "create"}
                    initialData={initialData || undefined}
                    loading={loading}
                    onSubmit={handleSubmit}
                    onDelete={isEdit ? handleDelete : undefined}
                    onCancel={() => navigate("/intents/list")}
                />
            )}
        </div>
    );
}