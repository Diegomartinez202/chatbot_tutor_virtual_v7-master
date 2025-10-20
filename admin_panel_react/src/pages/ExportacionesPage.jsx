// src/pages/ExportacionesPage.jsx
import React, { useMemo, useState } from "react";
import { FileText, Download, Search, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import toast from "react-hot-toast";
import { useQuery, useMutation } from "@tanstack/react-query";

import FiltrosFecha from "@/components/FiltrosFecha";
import { exportarCSV, fetchHistorialExportaciones } from "@/services/api";
import { formatDate } from "@/utils/formatDate";
import ExportacionesTable from "@/components/ExportacionesTable";
import IconTooltip from "@/components/ui/IconTooltip"; // ✅ tooltips reutilizables

function ExportacionesPage() {
    // ⬇️ fechas como strings (inputs controlados)
    const [desde, setDesde] = useState("");
    const [hasta, setHasta] = useState("");
    const [usuario, setUsuario] = useState("");
    const [tipo, setTipo] = useState("");

    const {
        data: historial = [],
        refetch,
        isFetching,
    } = useQuery({
        queryKey: ["historialExportaciones", usuario, tipo],
        queryFn: () => fetchHistorialExportaciones({ usuario, tipo }),
    });

    const exportMutation = useMutation({
        mutationFn: async () => exportarCSV(desde, hasta), // descarga directa (Blob)
        onSuccess: () => {
            toast.success("Exportación generada");
            refetch();
        },
        onError: () => toast.error("Error al exportar CSV"),
    });

    const filtered = useMemo(() => {
        const fi = desde ? new Date(desde).getTime() : null;
        const ff = hasta ? new Date(hasta).getTime() + 24 * 60 * 60 * 1000 - 1 : null; // incluir fin de día
        return (historial || []).filter((exp) => {
            const ts = exp.timestamp ? new Date(exp.timestamp).getTime() : null;
            const byFecha =
                (fi === null || (ts !== null && ts >= fi)) &&
                (ff === null || (ts !== null && ts <= ff));
            return byFecha;
        });
    }, [historial, desde, hasta]);

    const handleDescargar = (url) => {
        if (!url) return toast.error("Archivo no disponible");
        const a = document.createElement("a");
        a.href = url;
        a.target = "_blank";
        a.rel = "noopener";
        a.download = url.split("/").pop();
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    return (
        <div className="p-6 space-y-6">
            <h1 className="text-2xl font-bold flex items-center gap-2">
                <IconTooltip label="Exportaciones realizadas" side="top">
                    <FileText size={22} />
                </IconTooltip>
                Exportaciones realizadas
            </h1>

            {/* 🎯 Filtros */}
            <div className="flex flex-wrap gap-2 items-end">
                <FiltrosFecha
                    desde={desde}
                    hasta={hasta}
                    setDesde={setDesde}
                    setHasta={setHasta}
                />

                <input
                    type="text"
                    placeholder="Filtrar por usuario (email)"
                    className="border px-3 py-2 rounded-md"
                    value={usuario}
                    onChange={(e) => e.target.value.length <= 120 && setUsuario(e.target.value)}
                />

                <input
                    type="text"
                    placeholder="Filtrar por tipo"
                    className="border px-3 py-2 rounded-md"
                    value={tipo}
                    onChange={(e) => e.target.value.length <= 60 && setTipo(e.target.value)}
                />

                <IconTooltip label="Buscar en historial" side="top">
                    <Button onClick={() => refetch()} disabled={isFetching} type="button">
                        <Search className="w-4 h-4 mr-1" />
                        {isFetching ? "Buscando..." : "Buscar"}
                    </Button>
                </IconTooltip>

                <IconTooltip label="Generar exportación CSV" side="top">
                    <Button
                        onClick={() => exportMutation.mutate()}
                        disabled={exportMutation.isLoading}
                        className="ml-auto flex gap-2"
                        type="button"
                    >
                        <Download className="w-4 h-4" />
                        {exportMutation.isLoading ? "Exportando..." : "Exportar CSV"}
                    </Button>
                </IconTooltip>
            </div>

            {/* 📊 Tabla de resultados */}
            <h3 className="text-lg font-semibold mt-8 flex items-center gap-2">
                <IconTooltip label="Historial de exportaciones" side="top">
                    <History size={18} />
                </IconTooltip>
                Historial de Exportaciones
            </h3>

            <ExportacionesTable
                rows={filtered}
                onDownload={(row) => handleDescargar(row.url || row.endpoint)}
                formatDate={formatDate}
            />
        </div>
    );
}

export default ExportacionesPage;