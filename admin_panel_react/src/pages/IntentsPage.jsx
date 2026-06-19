// src/pages/IntentsPage.jsx
import React from "react";
import { useAuth } from "@/context/AuthContext";
import BotonesAdmin from "@/components/BotonesAdmin";
import IntentsForm from "@/components/IntentsForm";
import IntentsTable from "@/components/IntentsTable";
import { Brain, Lock } from "lucide-react";
import * as Tooltip from "@radix-ui/react-tooltip";

function IntentsPage() {
    const { user } = useAuth(); // ✅ Autenticación

    return (
        <div className="p-6 space-y-4">
            {/* 🧠 Título con ícono y tooltip */}
            <div className="flex items-center gap-2">
                <Tooltip.Provider delayDuration={200} skipDelayDuration={150}>
                    <Tooltip.Root>
                        <Tooltip.Trigger asChild>
                            <Brain className="w-6 h-6 text-gray-700" />
                        </Tooltip.Trigger>
                        <Tooltip.Portal>
                            <Tooltip.Content
                                className="rounded-md bg-black/90 text-white text-xs px-2 py-1 shadow"
                                side="top"
                                sideOffset={6}
                            >
                                Gestión de intents del chatbot
                                <Tooltip.Arrow className="fill-black/90" />
                            </Tooltip.Content>
                        </Tooltip.Portal>
                    </Tooltip.Root>
                </Tooltip.Provider>
                <h1 className="text-2xl font-bold">Gestión de Intents</h1>
            </div>

            {/* 🔘 Botones de administración */}
            {(user?.rol === "admin" || user?.rol === "soporte") && (
                <BotonesAdmin />
            )}

            {/* 🎯 Control de permisos para cargar intents */}
            {(user?.rol === "admin" || user?.rol === "soporte") ? (
                <IntentsForm />
            ) : (
                <div
                    className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-2 rounded-md flex items-center gap-2"
                    role="alert"
                >
                    <Lock className="w-4 h-4" />
                    No tienes permisos para cargar o editar intents.
                </div>
            )}

            {/* 📋 Tabla de intents siempre visible */}
            <IntentsTable />
        </div>
    );
}

export default IntentsPage;