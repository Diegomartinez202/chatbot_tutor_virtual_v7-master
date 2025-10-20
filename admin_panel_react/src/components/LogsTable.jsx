import React, { useEffect, useMemo, useState } from "react";
import { getLogsList } from "@/services/api";
import IconTooltip from "@/components/ui/IconTooltip";
import {
    Calendar,
    User,
    Route,
    Wrench,
    Shield,
    Globe,
    Compass,
    CheckCircle,
    MessageSquare,
    Download,
} from "lucide-react";
import { formatDate } from "@/utils/formatDate";
import { exportToCsv } from "@/utils/exportCsvHelper";
import Badge from "@/components/Badge";

/**
 * Tabla de logs con filtros opcionales y export a CSV de la vista filtrada.
 * - Usa lucide-react para íconos
 * - Tooltips con IconTooltip (Radix)
 * - Badges (modo estático) para endpoint/rol/status/intent
 * - Loading skeleton y estado vacío
 */
export default function LogsTable({
    filters = { email: "", endpoint: "", rol: "" },
    fechas = { fechaInicio: "", fechaFin: "" },
}) {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    // Carga inicial
    useEffect(() => {
        let mounted = true;
        (async () => {
            try {
                const data = await getLogsList();
                if (!mounted) return;
                setLogs(Array.isArray(data) ? data : []);
            } catch (error) {
                console.error("Error al cargar logs:", error);
                if (mounted) setLogs([]);
            } finally {
                if (mounted) setLoading(false);
            }
        })();
        return () => {
            mounted = false;
        };
    }, []);

    // Filtro por texto y rango de fechas
    const filteredLogs = useMemo(() => {
        const fi = fechas?.fechaInicio ? new Date(fechas.fechaInicio).getTime() : null;
        const ff = fechas?.fechaFin ? new Date(fechas.fechaFin).getTime() : null;

        return (logs || []).filter((log) => {
            const email = (log.email || log.user_email || "").toLowerCase();
            const endpoint = (log.endpoint || "").toLowerCase();
            const rol = (log.rol || log.role || "").toLowerCase();
            const ts = log.timestamp ? new Date(log.timestamp).getTime() : null;

            const matchEmail = email.includes((filters.email || "").toLowerCase());
            const matchEndpoint = endpoint.includes((filters.endpoint || "").toLowerCase());
            const matchRol = rol.includes((filters.rol || "").toLowerCase());

            const matchFecha =
                (fi === null || (ts !== null && ts >= fi)) &&
                (ff === null || (ts !== null && ts <= ff));

            return matchEmail && matchEndpoint && matchRol && matchFecha;
        });
    }, [logs, filters, fechas]);

    // Filas ya mapeadas para export
    const exportRows = useMemo(() => {
        return filteredLogs.map((l) => ({
            fecha: formatDate(l.timestamp, { withTime: true }),
            email: l.email || l.user_email || l.user_id || "",
            endpoint: l.endpoint || "",
            metodo: l.method || "",
            rol: l.rol || l.role || "",
            ip: l.ip || l.ip_address || "",
            user_agent: l.user_agent || "",
            status: l.status || "",
            intent: l.intent || "",
        }));
    }, [filteredLogs]);

    const handleExport = () => {
        if (!exportRows.length) return;
        exportToCsv(
            exportRows,
            `logs_${Date.now()}.csv`,
            ["fecha", "email", "endpoint", "metodo", "rol", "ip", "user_agent", "status", "intent"]
        );
    };

    // Loading skeleton
    if (loading) {
        return (
            <div className="rounded-md border border-gray-200 p-4">
                <div className="h-4 w-48 bg-gray-200 animate-pulse rounded mb-3" />
                <div className="space-y-2">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-10 w-full bg-gray-100 animate-pulse rounded" />
                    ))}
                </div>
            </div>
        );
    }

    // Empty state
    if (!filteredLogs.length) {
        return (
            <div className="rounded-md border border-gray-200 p-6 text-center text-gray-500">
                No hay registros coincidentes.
            </div>
        );
    }

    return (
        <div className="overflow-x-auto rounded-md shadow border border-gray-200">
            <div className="flex items-center justify-between p-3">
                <div className="text-sm text-gray-600">
                    Mostrando <strong>{filteredLogs.length}</strong>{" "}
                    {filteredLogs.length === 1 ? "registro" : "registros"}
                </div>
                <IconTooltip label="Exporta los registros filtrados actualmente" side="top">
                    <button
                        onClick={handleExport}
                        disabled={!exportRows.length}
                        className="flex items-center gap-2 text-sm px-3 py-2 border rounded bg-white hover:bg-gray-100 shadow disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label="Exportar CSV de la vista filtrada"
                    >
                        <Download className="w-4 h-4" aria-hidden="true" />
                        Exportar CSV (vista)
                    </button>
                </IconTooltip>
            </div>

            <table className="min-w-full table-auto bg-white text-sm">
                <thead className="bg-gray-100 text-gray-700">
                    <tr>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <Calendar size={16} aria-hidden="true" /> Fecha
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <User size={16} aria-hidden="true" /> Usuario
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <Route size={16} aria-hidden="true" /> Endpoint
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <Wrench size={16} aria-hidden="true" /> Método
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <Shield size={16} aria-hidden="true" /> Rol
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <Globe size={16} aria-hidden="true" /> IP
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <Compass size={16} aria-hidden="true" /> User-Agent
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <CheckCircle size={16} aria-hidden="true" /> Status
                            </span>
                        </th>
                        <th scope="col" className="px-4 py-2 text-left">
                            <span className="inline-flex items-center gap-2">
                                <MessageSquare size={16} aria-hidden="true" /> Intent
                            </span>
                        </th>
                    </tr>
                </thead>

                <tbody>
                    {filteredLogs.map((log, index) => {
                        const key = log._id || index;
                        const role = String(log.rol || log.role || "usuario").toLowerCase();
                        const status = String(log.status || "ok").toLowerCase();
                        const intent = String(log.intent || "default").toLowerCase();
                        const ua = log.user_agent || "—";

                        return (
                            <tr key={key} className="border-t border-gray-200 hover:bg-gray-50">
                                <td className="px-4 py-2 whitespace-nowrap">
                                    {log.timestamp ? formatDate(log.timestamp, { withTime: true }) : "—"}
                                </td>
                                <td className="px-4 py-2">
                                    {log.email || log.user_email || log.user_id || "—"}
                                </td>
                                <td className="px-4 py-2">
                                    <Badge mode="static" value={log.endpoint || "—"} />
                                </td>
                                <td className="px-4 py-2">{log.method || "—"}</td>
                                <td className="px-4 py-2">
                                    <Badge mode="static" type="role" value={role} />
                                </td>
                                <td className="px-4 py-2">{log.ip || log.ip_address || "—"}</td>
                                <td className="px-4 py-2 max-w-[260px]">
                                    <IconTooltip label={ua} side="top">
                                        <span className="block truncate cursor-help">{ua}</span>
                                    </IconTooltip>
                                </td>
                                <td className="px-4 py-2">
                                    <Badge mode="static" type="status" value={status} />
                                </td>
                                <td className="px-4 py-2">
                                    <Badge mode="static" type="intent" value={intent} />
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}