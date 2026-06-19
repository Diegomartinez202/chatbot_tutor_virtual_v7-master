// src/components/TrainBotButton.jsx
import React from "react";
import { Button } from "@/components/ui";
import IconTooltip from "@/components/ui/IconTooltip";
import { useAdminActions } from "@/services/useAdminActions";
import { Cog, Loader2 } from "lucide-react";
import { apiClient } from "@/services/apiClient"; // ✅ Para consultar el último modelo

function TrainBotButton({
    className = "",
    variant = "default",
    size = "default",
    tooltipLabel = "Reentrenar modelo del bot",
    onTrained, // callback opcional
    mode,
    branch,
}) {
    const { trainMutation } = useAdminActions();

    const handleTrain = async () => {
        try {
            const payload = mode ? { mode, branch: branch || "main" } : undefined;
            trainMutation.mutate(payload, {
                onSuccess: async (res) => {
                    if (typeof onTrained === "function") onTrained(res?.data || res);

                    // 🔔 Nuevo: feedback visual con info del modelo
                    try {
                        const modelRes = await apiClient.get("/api/admin/last-model");
                        const { model_name, timestamp } = modelRes.data || {};
                        if (model_name) {
                            alert(
                                `✅ Entrenamiento completado correctamente\n\nModelo: ${model_name}\nFecha: ${timestamp}`
                            );
                        } else {
                            alert("✅ Entrenamiento completado correctamente, sin modelo registrado aún.");
                        }
                    } catch (err) {
                        console.warn("⚠️ No se pudo obtener el modelo más reciente:", err);
                        alert("✅ Entrenamiento completado, pero no se pudo leer el modelo en Mongo.");
                    }
                },
                onError: (err) => {
                    console.error("❌ Error durante el entrenamiento:", err);
                    alert("❌ Error al entrenar el bot. Revisa los logs para más detalles.");
                },
            });
        } catch (e) {
            console.error("❌ Error inesperado:", e);
            alert("❌ Error inesperado al iniciar el entrenamiento.");
        }
    };

    return (
        <IconTooltip label={tooltipLabel} side="top">
            <span>
                <Button
                    onClick={handleTrain}
                    disabled={trainMutation.isPending}
                    variant={variant}
                    size={size}
                    className={className}
                    aria-label="Reentrenar bot"
                    aria-busy={trainMutation.isPending ? "true" : "false"}
                >
                    {trainMutation.isPending ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                        <Cog className="w-4 h-4 mr-2" />
                    )}
                    {trainMutation.isPending ? "Entrenando…" : "Reentrenar bot"}
                </Button>
            </span>
        </IconTooltip>
    );
}

export default TrainBotButton;
