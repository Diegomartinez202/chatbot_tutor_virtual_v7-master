// src/pages/ExportarLogsPage.jsx
import { useEffect, useState } from "react";
import { getExportStats } from "@/services/api";
import { format } from "date-fns";
import {
    Download,
    Calendar,
    User,
    FileText,
    ArrowDownCircle,
    AlertCircle,
} from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

function ExportarLogsPage() {
    const [exportaciones, setExportaciones] = useState([]);

    useEffect(() => {
        getExportStats()
            .then((data) => setExportaciones(Array.isArray(data) ? data : []))
            .catch(console.error);
    }, []);

    return (
        <div className="p-6 max-w-5xl mx-auto">
            {/* 🧾 Título con ícono */}
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Exportaciones de logs generadas" side="top">
                    <Download className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h1 className="text-2xl font-bold">Exportaciones de Logs</h1>
            </div>

            {exportaciones.length === 0 ? (
                <p className="text-gray-500 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    No hay exportaciones registradas.
                </p>
            ) : (
                <div className="overflow-x-auto border rounded shadow">
                    <table className="min-w-full text-sm bg-white">
                        <thead className="bg-gray-100 text-left">
                            <tr>
                                <th className="px-4 py-2">
                                    <IconTooltip label="Fecha de la exportación" side="top">
                                        <div className="flex items-center gap-1">
                                            <Calendar size={16} />
                                            <span>Fecha</span>
                                        </div>
                                    </IconTooltip>
                                </th>
                                <th className="px-4 py-2">
                                    <IconTooltip label="Usuario que exportó" side="top">
                                        <div className="flex items-center gap-1">
                                            <User size={16} />
                                            <span>Usuario</span>
                                        </div>
                                    </IconTooltip>
                                </th>
                                <th className="px-4 py-2">
                                    <IconTooltip label="Nombre del archivo generado" side="top">
                                        <div className="flex items-center gap-1">
                                            <FileText size={16} />
                                            <span>Archivo</span>
                                        </div>
                                    </IconTooltip>
                                </th>
                                <th className="px-4 py-2">
                                    <IconTooltip label="Descargar archivo" side="top">
                                        <div className="flex items-center gap-1">
                                            <ArrowDownCircle size={16} />
                                            <span>Acción</span>
                                        </div>
                                    </IconTooltip>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {exportaciones.map((exp, i) => (
                                <tr key={i} className="border-t hover:bg-gray-50">
                                    <td className="px-4 py-2">
                                        {exp.fecha ? format(new Date(exp.fecha), "yyyy-MM-dd HH:mm") : "—"}
                                    </td>
                                    <td className="px-4 py-2">{exp.usuario || "—"}</td>
                                    <td className="px-4 py-2">{exp.archivo}</td>
                                    <td className="px-4 py-2">
                                        <a
                                            href={`${import.meta.env.VITE_API_URL}/admin/logs/${exp.archivo}`}
                                            className="text-blue-600 hover:underline flex items-center gap-1"
                                            download
                                        >
                                            <Download size={16} /> Descargar
                                        </a>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default ExportarLogsPage;