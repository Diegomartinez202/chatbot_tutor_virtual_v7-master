// src/components/TrainBotButton.jsx
import React from "react";
import { Button } from "@/components/ui"; // ← barrel unificado
import IconTooltip from "@/components/ui/IconTooltip";
import { useAdminActions } from "@/services/useAdminActions";
import { Cog, Loader2 } from "lucide-react";

function TrainBotButton({
    className = "",
    variant = "default",
    size = "default",
    tooltipLabel = "Reentrenar modelo del bot",
    onTrained, // opcional: callback tras éxito
    mode,      // opcional: "local" | "ci"
    branch,    // opcional: rama para CI
}) {
    const { trainMutation } = useAdminActions();

    const handleTrain = () => {
        const payload = mode ? { mode, branch: branch || "main" } : undefined;
        trainMutation.mutate(payload, {
            onSuccess: (res) => {
                if (typeof onTrained === "function") onTrained(res?.data || res);
            },
        });
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