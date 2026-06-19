// src/components/FallbackLogsTable.jsx
import React, { useMemo, useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getFailedLogs, exportFailedIntentsCSV } from "@/services/api";
import { formatDate } from "@/utils/formatDate";
import {
    Download,
    ChevronLeft,
    ChevronRight,
    Calendar,
    User,
    MessageCircle,
    AlertTriangle,
    XCircle,
} from "lucide-react";
import { toast } from "react-hot-toast";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";
import { Button } from "@/components/ui/button";

/**
 * Props:
 * - desde: string "YYYY-MM-DD"
 * - hasta: string "YYYY-MM-DD"
 * - intents: [{ intent, count }] (opcional, para poblar dropdown)
 * - initialIntent: string (opcional)
 * - pageSize: number (opcional, default 20)
 * - onIntentChange: (value: string) => void (opcional)
 */
const FallbackLogsTable = ({
    desde = "",
    hasta = "",
    intents = [],
    initialIntent = "",
    pageSize = 20,
    onIntentChange,
}) => {
    const [intent, setIntent] = useState(initialIntent);
    const [page, setPage] = useState(1);

    // Mantén intent sincronizado si el padre cambia initialIntent
    useEffect(() => {
        setIntent(initialIntent || "");
        setPage(1);
    }, [initialIntent]);

    // Al cambiar el rango de fechas, vuelve a la primera página
    useEffect(() => {
        setPage(1);
    }, [desde, hasta]);

    const queryKey = useMemo(
        () => ["failedLogs", { desde, hasta, intent, page, page_size: pageSize }],
        [desde, hasta, intent, page, pageSize]
    );

    const { data, isFetching } = useQuery({
        queryKey,
        queryFn: async () => {
            const res = await getFailedLogs({
                desde,
                hasta,
                intent: intent || undefined,
                page,
                page_size: pageSize,
            });
            if (Array.isArray(res)) {
                return { items: res, total: res.length, page, page_size: pageSize };
            }
            return {
                items: Array.isArray(res?.items) ? res.items : [],
                total: Number(res?.total ?? 0),
                page: Number(res?.page ?? page),
                page_size: Number(res?.page_size ?? pageSize),
            };
        },
        keepPreviousData: true,
    });

    const rows = data?.items || [];
    const total = data?.total || 0;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));

    const exportMutation = useMutation({
        mutationFn: () =>
            exportFailedIntentsCSV({ desde, hasta, intent: intent || undefined }),
        onSuccess: () =>
            toast.success("CSV exportado", {
                icon: <Download className="w-4 h-4" />,
            }),
        onError: () =>
            toast.error("Error al exportar CSV", {
                icon: <XCircle className="w-4 h-4" />,
            }),
    });

    const intentsOptions = useMemo(() => {
        const base = intents?.map((i) => i?.intent).filter(Boolean) || [];
        return Array.from(new Set(base));
    }, [intents]);

    const changeIntent = (value) => {
        setIntent(value);
        setPage(1);
    };

    const prev = () => setPage((p) => Math.max(1, p - 1));
    const next = () => setPage((p) => Math.min(totalPages, p + 1));

    return (
        <div className="mt-6 space-y-3">
            {/* Filtros de tabla */}
            <div className="flex flex-wrap items-end gap-3">
                <div className="flex flex-col">
                    <label className="text-sm text-gray-600 mb-1">Intent</label>
                    <select
                        className="border px-3 py-2 rounded-md min-w-[220px]"
                        value={intent}
                        onChange={(e) => {
                            const v = e.target.value;
                            changeIntent(v);
                            onIntentChange?.(v);
                        }}
                    >
                        <option value="">Todos</option>
                        {intentsOptions.map((name) => (
                            <option key={name} value={name}>
                                {name}
                            </option>
                        ))}
                    </select>
                </div>

                <IconTooltip label="Exportar CSV con los filtros aplicados" side="top">
                    <Button
                        onClick={() => exportMutation.mutate()}
                        disabled={exportMutation.isLoading}
                        className="ml-auto inline-flex items-center gap-2"
                        type="button"
                        aria-busy={exportMutation.isLoading}
                    >
                        <Download size={16} />
                        {exportMutation.isLoading ? "Exportando..." : "Exportar CSV (filtros)"}
                    </Button>
                </IconTooltip>
            </div>

            {/* Tabla */}
            <div className="overflow-x-auto border rounded-md shadow bg-white">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-100 text-left">
                        <tr>
                            <th scope="col" className="px-4 py-2">
                                <span className="inline-flex items-center gap-1">
                                    <Calendar size={16} /> Fecha
                                </span>
                            </th>
                            <th scope="col" className="px-4 py-2">
                                <span className="inline-flex items-center gap-1">
                                    <User size={16} /> Usuario/Email
                                </span>
                            </th>
                            <th scope="col" className="px-4 py-2">
                                <span className="inline-flex items-center gap-1">
                                    <MessageCircle size={16} /> Mensaje
                                </span>
                            </th>
                            <th scope="col" className="px-4 py-2">
                                <span className="inline-flex items-center gap-1">
                                    <AlertTriangle size={16} /> Intent
                                </span>
                            </th>
                        </tr>
                    </thead>
                    <tbody aria-busy={isFetching}>
                        {isFetching ? (
                            <tr>
                                <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                                    Cargando…
                                </td>
                            </tr>
                        ) : rows.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                                    No hay registros.
                                </td>
                            </tr>
                        ) : (
                            rows.map((log, i) => (
                                <tr key={log._id || i} className="border-t hover:bg-gray-50">
                                    <td className="px-4 py-2 whitespace-nowrap">
                                        {formatDate(log.timestamp, { withTime: true }) || "—"}
                                    </td>
                                    <td className="px-4 py-2">
                                        {log.email || log.user_email || log.user_id || "—"}
                                    </td>
                                    <td className="px-4 py-2 max-w-[420px]">
                                        <IconTooltip label={log.message || log.text || "—"} side="top">
                                            <span className="block truncate cursor-help">
                                                {log.message || log.text || "—"}
                                            </span>
                                        </IconTooltip>
                                    </td>
                                    <td className="px-4 py-2">
                                        <Badge
                                            type="intent"
                                            value={log.intent || log.predicted_intent || "—"}
                                        />
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Paginación */}
            <div className="flex justify-center items-center gap-3">
                <Button
                    onClick={prev}
                    disabled={page <= 1}
                    variant="secondary"
                    className="inline-flex items-center gap-1"
                    type="button"
                >
                    <ChevronLeft className="w-4 h-4" /> Anterior
                </Button>
                <span className="px-2 py-1 text-sm">
                    Página <strong>{total ? page : 0}</strong> de{" "}
                    <strong>{total ? totalPages : 0}</strong>
                </span>
                <Button
                    onClick={next}
                    disabled={page >= totalPages}
                    variant="secondary"
                    className="inline-flex items-center gap-1"
                    type="button"
                >
                    Siguiente <ChevronRight className="w-4 h-4" />
                </Button>
            </div>
        </div>
    );
};

export default FallbackLogsTable;