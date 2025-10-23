// src/components/ResumenSistema.jsx
import React, { useEffect, useState } from "react";
import { getStats } from "@/services/api";
import { Card, CardContent } from "@/components/ui/Card";
import Badge from "@/components/Badge";
import IconTooltip from "@/components/ui/IconTooltip";
import toast from "react-hot-toast";
import {
    FileText,
    Users,
    MessageSquare,
    Target,
    Shield,
    Clock,
    Info,
} from "lucide-react";

function Row({ icon: Icon, label, value, tooltip }) {
    return (
        <div className="flex items-center gap-2">
            <Icon className="w-4 h-4 text-gray-600" aria-hidden="true" />
            <span className="text-sm text-gray-700">{label}:</span>
            <strong className="text-sm">{value}</strong>
            {tooltip ? (
                <IconTooltip label={tooltip}>
                    <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                </IconTooltip>
            ) : null}
        </div>
    );
}

export default function ResumenSistema() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const data = await getStats();
                setStats(data || {});
            } catch (err) {
                console.error(err);
                toast.error("Error al cargar estadísticas");
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    if (loading) return <p className="text-gray-600">Cargando resumen…</p>;
    if (!stats) return <p className="text-gray-500">Sin datos de estadísticas.</p>;

    const intentsMasUsados = Array.isArray(stats.intents_mas_usados)
        ? stats.intents_mas_usados
        : [];
    const usuariosPorRol =
        stats.usuarios_por_rol && typeof stats.usuarios_por_rol === "object"
            ? stats.usuarios_por_rol
            : {};
    const ultimosUsuarios = Array.isArray(stats.ultimos_usuarios)
        ? stats.ultimos_usuarios
        : [];

    return (
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 mt-6">
            {/* Totales simples */}
            <Card>
                <CardContent className="p-4">
                    <Row
                        icon={FileText}
                        label="Total logs"
                        value={stats.total_logs ?? "—"}
                        tooltip="Cantidad total de registros en el sistema"
                    />
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-4">
                    <Row
                        icon={Users}
                        label="Total usuarios"
                        value={stats.total_usuarios ?? "—"}
                        tooltip="Usuarios registrados en la plataforma"
                    />
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-4">
                    <Row
                        icon={MessageSquare}
                        label="Intents definidos"
                        value={stats.total_intents ?? "—"}
                        tooltip="Cantidad de intents configurados"
                    />
                </CardContent>
            </Card>

            {/* Intents más usados */}
            <Card>
                <CardContent className="p-4 space-y-2">
                    <div className="flex items-center gap-2 font-semibold">
                        <Target className="w-4 h-4 text-gray-700" aria-hidden="true" />
                        <span>Intents más usados</span>
                        <IconTooltip label="Top intents con mayor cantidad de disparos">
                            <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                        </IconTooltip>
                    </div>

                    {intentsMasUsados.length ? (
                        <div className="space-y-1">
                            {intentsMasUsados.map((i, idx) => (
                                <div
                                    key={`${i.intent}-${idx}`}
                                    className="flex items-center justify-between text-sm"
                                >
                                    <span className="truncate">{i.intent}</span>
                                    {/* Badge como chip informativo estático */}
                                    <Badge value={String(i.count ?? 0)} />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-gray-500">No hay datos.</div>
                    )}
                </CardContent>
            </Card>

            {/* Usuarios por rol */}
            <Card>
                <CardContent className="p-4 space-y-2">
                    <div className="flex items-center gap-2 font-semibold">
                        <Shield className="w-4 h-4 text-gray-700" aria-hidden="true" />
                        <span>Usuarios por rol</span>
                        <IconTooltip label="Distribución de usuarios según su rol">
                            <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                        </IconTooltip>
                    </div>

                    {Object.keys(usuariosPorRol).length ? (
                        <div className="space-y-1">
                            {Object.entries(usuariosPorRol).map(([rol, cantidad], idx) => (
                                <div
                                    key={`${rol}-${idx}`}
                                    className="flex items-center justify-between text-sm"
                                >
                                    <span className="truncate">{rol}</span>
                                    <div className="flex items-center gap-2">
                                        <Badge type="role" value={String(rol).toLowerCase()} />
                                        <Badge value={String(cantidad ?? 0)} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-gray-500">No hay datos.</div>
                    )}
                </CardContent>
            </Card>

            {/* Últimos usuarios */}
            <Card>
                <CardContent className="p-4 space-y-2">
                    <div className="flex items-center gap-2 font-semibold">
                        <Clock className="w-4 h-4 text-gray-700" aria-hidden="true" />
                        <span>Últimos usuarios</span>
                        <IconTooltip label="Usuarios que ingresaron más recientemente">
                            <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                        </IconTooltip>
                    </div>

                    {ultimosUsuarios.length ? (
                        <div className="space-y-1">
                            {ultimosUsuarios.map((u, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between text-sm"
                                >
                                    <span className="truncate">
                                        {u?.nombre ?? u?.email ?? "—"}
                                    </span>
                                    {/* Chip “Nuevo” (estático) solo al primero */}
                                    {idx === 0 ? <Badge value="Nuevo" /> : null}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-sm text-gray-500">No hay usuarios recientes.</div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}