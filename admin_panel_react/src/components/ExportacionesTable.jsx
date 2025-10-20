// src/components/ExportacionesTable.jsx
import React from "react";
import { Download, FileText, Tag, CalendarClock, User } from "lucide-react";

const ExportacionesTable = ({ rows = [], onDownload, formatDate }) => {
    return (
        <div className="overflow-x-auto mt-2">
            <table className="min-w-full text-sm border border-gray-200 dark:border-gray-700">
                <thead className="bg-gray-100 dark:bg-gray-800 dark:text-white">
                    <tr>
                        <th className="text-left px-4 py-2">
                            <span className="inline-flex items-center gap-2">
                                <FileText size={14} /> Archivo
                            </span>
                        </th>
                        <th className="text-left px-4 py-2">
                            <span className="inline-flex items-center gap-2">
                                <Tag size={14} /> Tipo
                            </span>
                        </th>
                        <th className="text-left px-4 py-2">
                            <span className="inline-flex items-center gap-2">
                                <CalendarClock size={14} /> Fecha
                            </span>
                        </th>
                        <th className="text-left px-4 py-2">
                            <span className="inline-flex items-center gap-2">
                                <User size={14} /> Usuario
                            </span>
                        </th>
                        <th className="text-left px-4 py-2">Descargar</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.length === 0 ? (
                        <tr>
                            <td colSpan={5} className="px-4 py-3 text-center text-gray-500">
                                No se encontraron exportaciones.
                            </td>
                        </tr>
                    ) : (
                        rows.map((exp, i) => (
                            <tr
                                key={i}
                                className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                            >
                                <td className="px-4 py-2">{exp.nombre_archivo || "—"}</td>
                                <td className="px-4 py-2">{exp.tipo || "—"}</td>
                                <td className="px-4 py-2">
                                    {exp.timestamp ? formatDate(exp.timestamp, { withTime: true }) : "—"}
                                </td>
                                <td className="px-4 py-2">{exp.email || "Anónimo"}</td>
                                <td className="px-4 py-2">
                                    {exp.url || exp.endpoint ? (
                                        <button
                                            onClick={() => onDownload?.(exp)}
                                            className="flex items-center gap-1 text-blue-600 hover:underline"
                                        >
                                            <Download size={14} /> Descargar
                                        </button>
                                    ) : (
                                        <span className="text-gray-400 italic">No disponible</span>
                                    )}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default ExportacionesTable;