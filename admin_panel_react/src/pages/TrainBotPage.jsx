// src/pages/TrainBotPage.jsx
import React from "react";
import TrainBotButton from "@/components/TrainBotButton";
import { BrainCog } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

function TrainBotPage() {
    return (
        <div className="p-6 space-y-6">
            {/* Encabezado */}
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Entrenamiento del modelo conversacional" side="top">
                    <BrainCog className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h1 className="text-2xl font-bold">Reentrenar Chatbot</h1>
            </div>

            {/* Explicación */}
            <p className="text-gray-700 max-w-2xl">
                Este proceso reentrena el modelo Rasa con los intents actualizados. Asegúrate de haber
                cargado correctamente todos los datos antes de continuar. Este proceso puede tardar unos segundos.
            </p>

            {/* Botón para reentrenar */}
            <TrainBotButton />
        </div>
    );
}

export default TrainBotPage;