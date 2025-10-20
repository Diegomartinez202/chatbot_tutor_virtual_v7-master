// src/components/StatsChart.jsx
import React, { useEffect, useState, useMemo } from "react";
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip as ReTooltip,
    LineChart,
    Line,
    CartesianGrid,
    Cell,
    PieChart,
    Pie,
    Legend,
} from "recharts";
import { getStats } from "@/services/api";
import { toast } from "react-hot-toast";
import { motion } from "framer-motion";
import {
    Download,
    RefreshCw,
    BarChart2,
    Users as UsersIcon,
    FileText,
    Activity,
} from "lucide-react";
import { exportToCsv } from "@/utils/exportCsvHelper";
import { Button } from "@/components/ui/button";
import IconTooltip from "@/components/ui/IconTooltip";
import Badge from "@/components/Badge";

const COLORS = [
    "#4F46E5",
    "#10B981",
    "#FBBF24",
    "#EF4444",
    "#6366F1",
    "#22c55e",
    "#f97316",
];

function normalizeIntentsMasUsados(src) {
    const list = src?.intents_mas_usados ?? src?.top_intents ?? [];
    return (Array.isArray(list) ? list : []).map((i) => ({
        name: i.intent ?? i._id ?? "—",
        total: Number(i.total ?? i.count ?? 0),
    }));
}

function normalizeUsuariosPorRol(src) {
    const raw = src?.usuarios_por_rol;
    if (Array.isArray(raw))
        return raw.map((r) => ({
            rol: r.rol ?? r._id ?? "—",
            total: Number(r.total ?? r.count ?? 0),
        }));
    if (raw && typeof raw === "object") {
        return Object.entries(raw).map(([rol, total]) => ({
            rol,
            total: Number(total ?? 0),
        }));
    }
    return [];
}

function normalizeLogsPorDia(src) {
    const list = src?.logs_por_dia ?? [];
    return Array.isArray(list)
        ? list.map((d) => ({
            fecha: d.fecha ?? d._id ?? "—",
            total: Number(d.total ?? d.count ?? 0),
        }))
        : [];
}

function normalizeExportacionesPorDia(src) {
    const list =
        src?.exportaciones_por_dia ?? src?.exports_by_day ?? src?.csv_por_dia;
    if (Array.isArray(list)) {
        return list.map((d) => ({
            _id: d._id ?? d.fecha ?? "—",
            total: Number(d.total ?? d.count ?? 0),
        }));
    }
    if (list && typeof list === "object") {
        return Object.entries(list).map(([k, v]) => ({
            _id: k,
            total: Number(v ?? 0),
        }));
    }
    return [];
}

export default function StatsChart({ desde, hasta }) {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    const intentsData = useMemo(() => normalizeIntentsMasUsados(stats), [stats]);
    const usersByRole = useMemo(() => normalizeUsuariosPorRol(stats), [stats]);
    const logsPorDia = useMemo(() => normalizeLogsPorDia(stats), [stats]);
    const exportData = useMemo(
        () => normalizeExportacionesPorDia(stats),
        [stats]
    );

    const fetchData = async () => {
        try {
            setLoading(true);
            const statsRes = await getStats({ desde, hasta });
            setStats(statsRes || {});
        } catch (err) {
            console.error("Error al cargar estadísticas:", err);
            toast.error("Error al cargar estadísticas");
            setStats(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [desde, hasta]);

    if (loading)
        return (
            <p className="text-gray-600 dark:text-gray-300">Cargando estadísticas...</p>
        );
    if (!stats)
        return (
            <p className="text-red-600 dark:text-red-400">
                No se pudieron cargar las estadísticas
            </p>
        );

    const handleExportCSV = () => {
        if (!exportData.length) {
            toast.error("No hay datos para exportar");
            return;
        }
        exportToCsv(exportData, "exportaciones.csv", ["_id", "total"]);
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="grid gap-8 md:grid-cols-2"
        >
            {/* Acciones */}
            <div className="col-span-2 flex justify-end gap-3 mb-2">
                <IconTooltip label="Recargar estadísticas" side="top">
                    <Button
                        onClick={fetchData}
                        className="inline-flex items-center gap-2"
                        type="button"
                        aria-label="Recargar estadísticas"
                    >
                        <RefreshCw size={16} /> Recargar
                    </Button>
                </IconTooltip>
                <IconTooltip label="Exportar CSV (exportaciones por día)" side="top">
                    <Button
                        onClick={handleExportCSV}
                        className="inline-flex items-center gap-2"
                        type="button"
                        aria-label="Exportar CSV"
                    >
                        <Download size={16} /> Exportar CSV
                    </Button>
                </IconTooltip>
            </div>

            {/* Resumen general */}
            <motion.div whileHover={{ scale: 1.02 }}>
                <h2 className="font-semibold text-lg mb-2 dark:text-white flex items-center gap-2">
                    <IconTooltip label="Resumen general" side="top">
                        <BarChart2 className="w-4 h-4" />
                    </IconTooltip>
                    Resumen general
                </h2>
                <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300">
                    <li>
                        <strong>Conversaciones:</strong> {stats.total_logs ?? "—"}
                    </li>
                    <li>
                        <strong>Usuarios registrados:</strong> {stats.total_usuarios ?? "—"}
                    </li>
                    <li>
                        <strong>Exportaciones CSV:</strong>{" "}
                        {stats.total_exportaciones_csv ?? "—"}
                    </li>
                </ul>
            </motion.div>

            {/* Intents más usados */}
            <motion.div whileHover={{ scale: 1.02 }}>
                <h2 className="font-semibold text-lg mb-2 dark:text-white flex items-center gap-2">
                    <IconTooltip label="Intents con mayor frecuencia" side="top">
                        <Activity className="w-4 h-4" />
                    </IconTooltip>
                    Intents más usados
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={intentsData}>
                        <XAxis dataKey="name" stroke="#8884d8" />
                        <YAxis allowDecimals={false} />
                        <ReTooltip />
                        <Bar dataKey="total">
                            {intentsData.map((_, index) => (
                                <Cell key={index} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </motion.div>

            {/* Usuarios por rol */}
            <motion.div whileHover={{ scale: 1.02 }}>
                <h2 className="font-semibold text-lg mb-2 dark:text-white flex items-center gap-2">
                    <IconTooltip label="Usuarios agrupados por rol" side="top">
                        <UsersIcon className="w-4 h-4" />
                    </IconTooltip>
                    Usuarios por rol
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie
                            data={usersByRole}
                            dataKey="total"
                            nameKey="rol"
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            label
                        >
                            {(usersByRole ?? []).map((_, index) => (
                                <Cell key={index} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </motion.div>

            {/* Logs por día */}
            <motion.div whileHover={{ scale: 1.02 }}>
                <h2 className="font-semibold text-lg mb-2 dark:text-white flex items-center gap-2">
                    <IconTooltip label="Cantidad de logs por día" side="top">
                        <BarChart2 className="w-4 h-4" />
                    </IconTooltip>
                    Logs por día
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={logsPorDia}>
                        <XAxis dataKey="fecha" />
                        <YAxis allowDecimals={false} />
                        <ReTooltip />
                        <CartesianGrid strokeDasharray="3 3" />
                        <Line type="monotone" dataKey="total" stroke="#6366F1" name="Logs" />
                    </LineChart>
                </ResponsiveContainer>
            </motion.div>

            {/* Exportaciones por día */}
            <motion.div whileHover={{ scale: 1.02 }}>
                <h2 className="font-semibold text-lg mb-2 dark:text-white flex items-center gap-2">
                    <IconTooltip label="Exportaciones CSV por día" side="top">
                        <FileText className="w-4 h-4" />
                    </IconTooltip>
                    Exportaciones por día
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={exportData}>
                        <XAxis dataKey="_id" />
                        <YAxis allowDecimals={false} />
                        <ReTooltip />
                        <CartesianGrid strokeDasharray="3 3" />
                        <Line
                            type="monotone"
                            dataKey="total"
                            stroke="#10B981"
                            name="Exportaciones"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </motion.div>

            {/* Últimos usuarios */}
            <motion.div className="col-span-2" whileHover={{ scale: 1.01 }}>
                <h2 className="font-semibold text-lg mb-2 dark:text-white">
                    Últimos usuarios registrados
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full border border-gray-300 dark:border-gray-600 rounded text-sm">
                        <thead>
                            <tr className="bg-gray-100 dark:bg-gray-800">
                                <th className="p-2 text-left">Correo</th>
                                <th className="p-2 text-left">Rol</th>
                                <th className="p-2 text-left">ID</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(stats.ultimos_usuarios ?? []).map((u, index) => (
                                <tr key={index} className="border-t dark:border-gray-700">
                                    <td className="p-2 text-gray-700 dark:text-gray-200">
                                        {u.email}
                                    </td>
                                    <td className="p-2">
                                        {/* Badge estático (NO es el contador del chat) */}
                                        <Badge type="role" value={u.rol} />
                                    </td>
                                    <td className="p-2 text-xs text-gray-500 dark:text-gray-400">
                                        {u._id}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </motion.div>
        </motion.div>
    );
}