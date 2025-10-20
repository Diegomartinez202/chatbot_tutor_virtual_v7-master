// src/pages/TestHistoryPage.jsx
import { useEffect, useState } from "react";
import { getTestHistory } from "@/services/api";
import { toast } from "react-hot-toast";
import IconTooltip from "@/components/ui/IconTooltip";
import { History, CheckCircle, XCircle } from "lucide-react";

const TestHistoryPage = () => {
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const data = await getTestHistory();
                setLogs(Array.isArray(data) ? data : []);
            } catch (err) {
                toast.error("Error al cargar historial", {
                    icon: <XCircle className="w-4 h-4" />,
                });
            }
        };
        fetchLogs();
    }, []);

    return (
        <div className="p-4">
            {/* Título con icono + tooltip */}
            <div className="flex items-center gap-2 mb-4">
                <IconTooltip label="Historial de pruebas ejecutadas" side="top">
                    <History className="w-6 h-6 text-gray-700" />
                </IconTooltip>
                <h2 className="text-2xl font-bold">Historial de Pruebas</h2>
            </div>

            <table className="w-full border">
                <thead>
                    <tr className="bg-gray-800 text-white">
                        <th className="p-2">Fecha</th>
                        <th className="p-2">Prueba</th>
                        <th className="p-2">Resultado</th>
                    </tr>
                </thead>
                <tbody>
                    {logs.map((log, i) => {
                        const ok = !!log.success;
                        return (
                            <tr key={i} className="text-center border-t">
                                <td className="p-2">
                                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}
                                </td>
                                <td className="p-2">{log.test_name || "—"}</td>
                                <td className="p-2">
                                    {ok ? (
                                        <span className="inline-flex items-center gap-1 text-green-600">
                                            <CheckCircle className="w-4 h-4" />
                                            Éxito
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-red-600">
                                            <XCircle className="w-4 h-4" />
                                            Fallo
                                        </span>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                    {logs.length === 0 && (
                        <tr>
                            <td colSpan={3} className="p-4 text-gray-500">
                                No hay registros disponibles.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default TestHistoryPage;