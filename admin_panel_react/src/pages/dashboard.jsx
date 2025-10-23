import React, { useState } from "react";
import { Link } from "react-router-dom";
import { LayoutDashboard, BarChart, Calendar, X } from "lucide-react";

import BotonesAdmin from "@/components/BotonesAdmin";
import ResumenSistema from "@/components/ResumenSistema";
import StatsChart from "@/components/StatsChart";
import IconTooltip from "@/components/ui/IconTooltip";
import { Button } from "@/components/ui/index.js"; 

function Dashboard() {
    const [desde, setDesde] = useState("");
    const [hasta, setHasta] = useState("");

    const clearDates = () => {
        setDesde("");
        setHasta("");
    };

    return (
        <div className="p-6 space-y-6">
            {/* Encabezado */}
            <div className="flex items-center gap-2">
                <IconTooltip label="Vista general del administrador" side="top">
                    <LayoutDashboard className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h1 className="text-2xl font-bold">Panel de Administración</h1>
            </div>

            {/* Acciones principales */}
            <BotonesAdmin />

            {/* Atajo a la página dedicada de estadísticas */}
            <Link
                to="/stats-v2"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
            >
                <BarChart size={18} /> Ver estadísticas v2
            </Link>

            {/* Resumen compacto */}
            <ResumenSistema />

            {/* Filtros de fecha (opcional) */}
            <div className="mt-4 rounded-md border bg-white p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <IconTooltip label="Filtrar por rango de fechas (opcional)" side="top">
                            <Calendar className="w-4 h-4 text-gray-600" />
                        </IconTooltip>
                        <h2 className="text-lg font-semibold">Estadísticas</h2>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex items-center gap-2">
                            <label className="text-sm text-gray-600">Desde</label>
                            <input
                                type="date"
                                value={desde}
                                onChange={(e) => setDesde(e.target.value)}
                                className="border rounded px-2 py-1 text-sm"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <label className="text-sm text-gray-600">Hasta</label>
                            <input
                                type="date"
                                value={hasta}
                                onChange={(e) => setHasta(e.target.value)}
                                className="border rounded px-2 py-1 text-sm"
                            />
                        </div>

                        <IconTooltip label="Limpiar fechas" side="top">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={clearDates}
                                className="inline-flex items-center gap-2"
                                aria-label="Limpiar rango de fechas"
                            >
                                <X className="w-4 h-4" /> Limpiar
                            </Button>
                        </IconTooltip>
                    </div>
                </div>

                <StatsChart desde={desde || undefined} hasta={hasta || undefined} />
            </div>
        </div>
    );
}

export default Dashboard;