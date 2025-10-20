// src/pages/Unauthorized.jsx
import IconTooltip from "@/components/ui/IconTooltip";
import { Lock, Home } from "lucide-react";
import { Link } from "react-router-dom";

function Unauthorized() {
    return (
        <div className="p-6 text-center" role="alert" aria-live="polite">
            <div className="flex items-center justify-center gap-2 mb-4">
                <IconTooltip label="Acceso denegado" side="top">
                    <Lock className="w-7 h-7 text-red-600" />
                </IconTooltip>
                <h1 className="text-3xl font-bold text-red-600">Acceso Denegado</h1>
            </div>

            <p className="text-gray-700 text-lg">
                No tienes permisos para acceder a esta sección del sistema.
            </p>

            {/* 🔹 Atajo opcional: volver a Inicio */}
            <div className="mt-6">
                <Link
                    to="/"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded bg-gray-900 text-white hover:bg-gray-800"
                >
                    <Home size={18} />
                    Volver al inicio
                </Link>
            </div>
        </div>
    );
}

export default Unauthorized;