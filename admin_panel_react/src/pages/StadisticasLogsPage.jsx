// src/pages/StadisticasLogsPage.jsx

import { useEffect, useState } from "react";
import { getExportStats } from "@/services/api";
import {
    BarChart as RechartsBarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";
import { BarChart3 } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

const StadisticasLogsPage = () => {
    const [data, setData] = useState([]);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const result = await getExportStats();
                const obj = result && typeof result === "object" ? result : {};
                const formatted = Object.entries(obj).map(([date, count]) => ({
                    fecha: date,
                    exportaciones: count,
                }));
                setData(formatted);
            } catch (error) {
                console.error("Error al cargar estadísticas:", error);
                setData([]);
            }
        };
        fetchStats();
    }, []);

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center gap-2">
                <IconTooltip label="Estadísticas de exportaciones de logs" side="top">
                    <BarChart3 className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h1 className="text-2xl font-bold">Estadísticas de Exportaciones de Logs</h1>
            </div>

            {data.length === 0 ? (
                <p className="text-gray-600">No hay exportaciones registradas aún.</p>
            ) : (
                <div className="w-full h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <RechartsBarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="fecha" />
                            <YAxis allowDecimals={false} />
                            <RechartsTooltip />
                            <Legend />
                            <Bar dataKey="exportaciones" fill="#4F46E5" />
                        </RechartsBarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default StadisticasLogsPage;