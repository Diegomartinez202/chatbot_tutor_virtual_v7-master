import React from "react";
import { useNavigate } from "react-router-dom";
import ExportIntentsButton from "@/components/ExportIntentsButton"; // ✅ corregido
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import { PlusCircle, Search } from "lucide-react";

function IntentNavBar() {
    const navigate = useNavigate();

    return (
        <div className="flex flex-wrap items-center gap-3 mb-4">
            <IconTooltip label="Crear un nuevo intent" side="top">
                <Button
                    variant="outline"
                    onClick={() => navigate("/intents")}
                    aria-label="Crear intent"
                    className="inline-flex items-center gap-2"
                >
                    <PlusCircle className="w-4 h-4" />
                    <span>Crear Intent</span>
                </Button>
            </IconTooltip>

            <IconTooltip label="Buscar o filtrar intents" side="top">
                <Button
                    variant="outline"
                    onClick={() => navigate("/intents/buscar")}
                    aria-label="Buscar intents"
                    className="inline-flex items-center gap-2"
                >
                    <Search className="w-4 h-4" />
                    <span>Buscar Intents</span>
                </Button>
            </IconTooltip>

            {/* El botón de exportación ya maneja su propia lógica/tooltip si lo deseas */}
            <ExportIntentsButton />
        </div>
    );
}

export default IntentNavBar;