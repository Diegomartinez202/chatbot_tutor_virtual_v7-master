// src/pages/StatsPage.jsx
import React, { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import BotonesAdmin from "@/components/BotonesAdmin";
import DateRangeFilter from "@/components/DateRangeFilter";
import StatsChart from "@/components/StatsChart";
import { BarChart2, Lock, FileText, Users, Download, Brain, XCircle } from "lucide-react";
import * as Tooltip from "@radix-ui/react-tooltip";
import toast from "react-hot-toast";
import { getStats } from "@/services/api";
import { useAdminActions } from "@/services/useAdminActions";
import Badge from "@/components/Badge";

function StatsPage() {
    const { user } = useAuth();
    const { exportTestsMutation } = useAdminActions();
    const [stats, setStats] = useState(null);
    const [desde, setDesde] = useState("");
    const [hasta, setHasta] = useState("");

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await getStats({ desde, hasta });
                setStats(data);
            } catch (err) {
                console.error("Error cargando estadísticas", err);
                toast.error("Error al obtener estadísticas", {
                    icon: <XCircle className="w-4 h-4" />,
                });
                setStats(null);
            }
        };
        fetchStats();
    }, [desde, hasta]);

    const isAllowed = user?.rol === "admin" || user?.rol === "soporte";

    return (
        <div className="p-6 space-y-6">
            <h1 className="text-2xl font-bold flex items-center gap-2">
                <BarChart2 size={22} /> Estadísticas del Chatbot
            </h1>

            {isAllowed ? (
                <>
                    <BotonesAdmin />

                    <DateRangeFilter
                        desde={desde}
                        hasta={hasta}
                        setDesde={setDesde}
                        setHasta={setHasta}
                    />

                    <div className="mt-4 flex justify-end">
                        <Tooltip.Provider delayDuration={200} skipDelayDuration={150}>
                            <Tooltip.Root>
                                <Tooltip.Trigger asChild>
                                    <button
                                        onClick={() => exportTestsMutation.mutate()}
                                        className="flex items-center gap-2 text-sm px-4 py-2 border rounded bg-white hover:bg-gray-100 shadow"
                                    >
                                        <Download size={16} /> Exportar test_all.sh
                                    </button>
                                </Tooltip.Trigger>
                                <Tooltip.Portal>
                                    <Tooltip.Content
                                        className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                        side="bottom"
                                        sideOffset={6}
                                    >
                                        Descargar resultados del script test_all.sh
                                        <Tooltip.Arrow className="fill-black/90" />
                                    </Tooltip.Content>
                                </Tooltip.Portal>
                            </Tooltip.Root>
                        </Tooltip.Provider>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                        <Tooltip.Provider delayDuration={200} skipDelayDuration={150}>
                            <div className="bg-white shadow rounded-md p-4">
                                <Tooltip.Root>
                                    <Tooltip.Trigger asChild>
                                        <p className="text-gray-500 flex items-center gap-2 cursor-help">
                                            <FileText size={16} /> Total de logs
                                        </p>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="top"
                                            sideOffset={6}
                                        >
                                            Registros almacenados por el chatbot
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                                <p className="text-lg font-bold">{stats?.total_logs ?? "..."}</p>
                            </div>

                            <div className="bg-white shadow rounded-md p-4">
                                <Tooltip.Root>
                                    <Tooltip.Trigger asChild>
                                        <p className="text-gray-500 flex items-center gap-2 cursor-help">
                                            <Download size={16} /> Exportaciones CSV
                                        </p>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="top"
                                            sideOffset={6}
                                        >
                                            Cantidad de archivos descargados
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                                <p className="text-lg font-bold">{stats?.total_exportaciones_csv ?? "..."}</p>
                            </div>

                            <div className="bg-white shadow rounded-md p-4">
                                <Tooltip.Root>
                                    <Tooltip.Trigger asChild>
                                        <p className="text-gray-500 flex items-center gap-2 cursor-help">
                                            <Users size={16} /> Total usuarios
                                        </p>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="top"
                                            sideOffset={6}
                                        >
                                            Número total de usuarios en el sistema
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                                <p className="text-lg font-bold">{stats?.total_usuarios ?? "..."}</p>
                            </div>

                            <div className="bg-white shadow rounded-md p-4">
                                <Tooltip.Root>
                                    <Tooltip.Trigger asChild>
                                        <p className="text-gray-500 cursor-help">Últimos usuarios</p>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="top"
                                            sideOffset={6}
                                        >
                                            Últimos usuarios registrados
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                                <ul className="list-disc ml-5 text-xs">
                                    {(stats?.ultimos_usuarios ?? []).map((u, i) => (
                                        <li key={i}>{u?.email ?? "—"}</li>
                                    ))}
                                </ul>
                            </div>

                            <div className="bg-white shadow rounded-md p-4">
                                <Tooltip.Root>
                                    <Tooltip.Trigger asChild>
                                        <p className="text-gray-500 cursor-help">Usuarios por rol</p>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="top"
                                            sideOffset={6}
                                        >
                                            Distribución de roles en el sistema
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                                <ul className="list-disc ml-5 text-xs space-y-1">
                                    {(stats?.usuarios_por_rol ?? []).map((r, i) => (
                                        <li key={i} className="flex items-center gap-2">
                                            <Badge type="role" value={r.rol} />
                                            <span>{r.total}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="bg-white shadow rounded-md p-4 col-span-2">
                                <Tooltip.Root>
                                    <Tooltip.Trigger asChild>
                                        <p className="text-gray-500 flex items-center gap-2 cursor-help">
                                            <Brain size={16} /> Intents más usados
                                        </p>
                                    </Tooltip.Trigger>
                                    <Tooltip.Portal>
                                        <Tooltip.Content
                                            className="rounded-md bg-black/90 text-white px-2 py-1 text-xs shadow"
                                            side="top"
                                            sideOffset={6}
                                        >
                                            Intents con mayor frecuencia de uso
                                            <Tooltip.Arrow className="fill-black/90" />
                                        </Tooltip.Content>
                                    </Tooltip.Portal>
                                </Tooltip.Root>
                                <ul className="list-disc ml-5 text-xs space-y-1">
                                    {(stats?.intents_mas_usados ?? []).map((item, i) => (
                                        <li key={i} className="flex items-center gap-2">
                                            <Badge type="intent" value={item.intent} />
                                            <span>({item.total})</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </Tooltip.Provider>
                    </div>

                    <StatsChart desde={desde} hasta={hasta} />
                </>
            ) : (
                <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-2 rounded-md flex items-center gap-2">
                    <Lock size={16} /> Acceso restringido para tu rol (<strong>{user?.rol}</strong>)
                </div>
            )}
        </div>
    );
}

export default StatsPage;