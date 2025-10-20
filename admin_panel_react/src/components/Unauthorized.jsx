// src/pages/Unauthorized.jsx
import React from "react";
import { ShieldAlert } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

const Unauthorized = () => (
    <div className="p-6 text-center">
        <div
            className="inline-flex items-center gap-2 mb-3"
            role="alert"
            aria-live="polite"
        >
            <IconTooltip label="Acceso denegado" side="top">
                <ShieldAlert className="w-6 h-6 text-red-600" aria-hidden="true" />
            </IconTooltip>
            <h2 className="text-2xl font-bold text-red-600">Acceso denegado</h2>
        </div>

        <p className="text-gray-700">
            No tienes permisos suficientes para acceder a esta sección.
        </p>
    </div>
);

export default Unauthorized;
