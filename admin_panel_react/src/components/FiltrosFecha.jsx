// src/components/FiltrosFecha.jsx
import React, { useEffect, useId } from "react";
import { CalendarRange, RotateCcw } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

/**
 * Uso flexible:
 * 1) Con estado separado:
 *    <FiltrosFecha desde={desde} hasta={hasta} setDesde={setDesde} setHasta={setHasta} />
 *
 * 2) Con objeto filtros:
 *    const [filtros, setFiltros] = useState({ fechaInicio: "", fechaFin: "" });
 *    <FiltrosFecha filtros={filtros} setFiltros={setFiltros} />
 *
 * Props extra:
 *  - onChangeRange?: ({ desde, hasta, invalid }) => void
 *  - disabled?: boolean
 *  - allowClear?: boolean (default true)
 *  - idPrefix?: string (para ARIA; por defecto se genera)
 */
export default function FiltrosFecha(props) {
    const {
        filtros,
        setFiltros,
        desde: pDesde,
        hasta: pHasta,
        setDesde: pSetDesde,
        setHasta: pSetHasta,
        onChangeRange,
        disabled = false,
        allowClear = true,
        idPrefix,
        className = "",
    } = props;

    const autoId = useId();
    const baseId = idPrefix || `ff-${autoId}`;

    const isObjectMode = !!(filtros && setFiltros);

    const norm = (v) =>
        v instanceof Date
            ? new Date(v.getTime() - v.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
            : (v ?? "");

    const desde = isObjectMode ? norm(filtros?.fechaInicio) : norm(pDesde);
    const hasta = isObjectMode ? norm(filtros?.fechaFin) : norm(pHasta);

    const setDesde = (val) => {
        if (isObjectMode) setFiltros((prev) => ({ ...prev, fechaInicio: val }));
        else pSetDesde?.(val);
    };
    const setHasta = (val) => {
        if (isObjectMode) setFiltros((prev) => ({ ...prev, fechaFin: val }));
        else pSetHasta?.(val);
    };

    const invalid =
        Boolean(desde) && Boolean(hasta) && new Date(desde) > new Date(hasta);

    const clear = () => {
        setDesde("");
        setHasta("");
    };

    // Notificar cambios al host si se provee callback
    useEffect(() => {
        onChangeRange?.({ desde, hasta, invalid });
    }, [desde, hasta, invalid, onChangeRange]);

    return (
        <div className={`flex flex-wrap items-end gap-4 mb-4 ${className}`}>
            {/* Desde */}
            <div className="flex flex-col">
                <label
                    htmlFor={`${baseId}-desde`}
                    className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2"
                >
                    <CalendarRange className="w-4 h-4" />
                    Desde
                </label>
                <input
                    id={`${baseId}-desde`}
                    type="date"
                    value={desde}
                    onChange={(e) => setDesde(e.target.value)}
                    max={hasta || undefined}
                    disabled={disabled}
                    className={[
                        "border px-3 py-2 rounded-md text-sm",
                        "bg-white dark:bg-gray-800 dark:text-white",
                        "border-gray-300 dark:border-gray-600",
                        invalid ? "border-red-500 ring-1 ring-red-300" : "",
                        disabled ? "opacity-60 cursor-not-allowed" : "",
                    ].join(" ")}
                    aria-invalid={invalid ? "true" : "false"}
                    aria-describedby={invalid ? `${baseId}-error` : undefined}
                />
            </div>

            {/* Hasta */}
            <div className="flex flex-col">
                <label
                    htmlFor={`${baseId}-hasta`}
                    className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                >
                    Hasta
                </label>
                <input
                    id={`${baseId}-hasta`}
                    type="date"
                    value={hasta}
                    onChange={(e) => setHasta(e.target.value)}
                    min={desde || undefined}
                    disabled={disabled}
                    className={[
                        "border px-3 py-2 rounded-md text-sm",
                        "bg-white dark:bg-gray-800 dark:text-white",
                        "border-gray-300 dark:border-gray-600",
                        invalid ? "border-red-500 ring-1 ring-red-300" : "",
                        disabled ? "opacity-60 cursor-not-allowed" : "",
                    ].join(" ")}
                    aria-invalid={invalid ? "true" : "false"}
                    aria-describedby={invalid ? `${baseId}-error` : undefined}
                />
            </div>

            {/* Botón limpiar */}
            {allowClear && (
                <IconTooltip content="Limpiar rango de fechas" side="top">
                    <button
                        type="button"
                        onClick={clear}
                        disabled={disabled || (!desde && !hasta)}
                        className={[
                            "flex items-center gap-2 text-sm px-3 py-2 border rounded shadow",
                            "bg-white hover:bg-gray-100 dark:bg-gray-800",
                            "dark:border-gray-600 dark:hover:bg-gray-700",
                            disabled || (!desde && !hasta)
                                ? "opacity-60 cursor-not-allowed"
                                : "",
                        ].join(" ")}
                    >
                        <RotateCcw className="w-4 h-4" />
                        Limpiar
                    </button>
                </IconTooltip>
            )}

            {/* Error rango inválido */}
            {invalid && (
                <p
                    id={`${baseId}-error`}
                    className="text-xs text-red-600 mt-2 basis-full"
                    role="alert"
                    aria-live="polite"
                >
                    Rango inválido: <strong>Desde</strong> no puede ser mayor que{" "}
                    <strong>Hasta</strong>.
                </p>
            )}
        </div>
    );
}