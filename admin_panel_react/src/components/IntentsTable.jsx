import React, { useEffect, useState } from "react";
import { Eye, Pencil, Trash2, ArrowUp, ArrowDown, ChevronsUpDown } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

// 👉 Si luego conectas a tu API, puedes pasar intents por props.
//    Mientras tanto usamos un mock local como fallback.
const MOCK_INTENTS = [
    { id: "saludo", intent: "saludo", example: "Hola, ¿cómo estás?", response: "¡Hola! ¿En qué puedo ayudarte?" },
    { id: "despedida", intent: "despedida", example: "Adiós", response: "¡Hasta pronto!" },
];

/**
 * IntentsTable
 *
 * Props:
 * - intents: array (datos)
 * - onView(row), onEdit(row), onDelete(row)
 * - sortBy: "intent" | "example" | "response" | undefined
 * - sortDir: "asc" | "desc" | undefined
 * - onSortChange: (nextBy, nextDir) => void
 */
export default function IntentsTable({
    intents: intentsProp,
    onView,
    onEdit,
    onDelete,
    sortBy,
    sortDir,
    onSortChange,
}) {
    const [intents, setIntents] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        if (Array.isArray(intentsProp)) setIntents(intentsProp);
        else setIntents(MOCK_INTENTS);
    }, [intentsProp]);

    const resolveId = (row) => encodeURIComponent(row?.id || row?.intent || "");

    const handleView = (row) => {
        if (typeof onView === "function") return onView(row);
        const id = resolveId(row);
        if (!id) return toast.error("No se encontró el identificador del intent");
        navigate(`/intents/${id}`);
    };

    const handleEdit = (row) => {
        if (typeof onEdit === "function") return onEdit(row);
        const id = resolveId(row);
        if (!id) return toast.error("No se encontró el identificador del intent");
        navigate(`/intents/${id}/edit`);
    };

    const handleDelete = (rowIdx, row) => {
        if (typeof onDelete === "function") return onDelete(row);
        // Mock: elimina localmente
        setIntents((prev) => prev.filter((_, i) => i !== rowIdx));
        toast.success(`Intent "${row.intent}" eliminado (simulado)`);
    };

    const iconForSort = (key) => {
        if (sortBy !== key) return <ChevronsUpDown className="w-4 h-4 opacity-60" />;
        if (sortDir === "asc") return <ArrowUp className="w-4 h-4" />;
        if (sortDir === "desc") return <ArrowDown className="w-4 h-4" />;
        return <ChevronsUpDown className="w-4 h-4 opacity-60" />;
    };

    const handleSort = (key) => {
        if (!onSortChange) return;
        if (sortBy !== key) return onSortChange(key, "asc");
        const nextDir = sortDir === "asc" ? "desc" : "asc";
        onSortChange(key, nextDir);
    };

    const headerBtnCls =
        "inline-flex items-center gap-1.5 text-left hover:underline underline-offset-2";

    const ariaSort = (key) => {
        if (sortBy !== key) return "none";
        return sortDir === "asc" ? "ascending" : "descending";
        // valores válidos: "none" | "ascending" | "descending" | "other"
    };

    // Compat con datos reales (arrays) vs mock (string)
    const firstExample = (row) =>
        row.example ??
        (Array.isArray(row.examples) && row.examples.length ? row.examples[0] : "");
    const firstResponse = (row) =>
        row.response ??
        (Array.isArray(row.responses) && row.responses.length ? row.responses[0] : "");

    return (
        <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm border rounded-lg overflow-hidden">
                <thead className="bg-gray-100 text-left">
                    <tr>
                        <th className="p-2 border" aria-sort={ariaSort("intent")}>
                            <IconTooltip label="Ordenar por Intent" side="top">
                                <button
                                    type="button"
                                    onClick={() => handleSort("intent")}
                                    className={headerBtnCls}
                                    aria-label="Ordenar por Intent"
                                >
                                    Intent {iconForSort("intent")}
                                </button>
                            </IconTooltip>
                        </th>

                        <th className="p-2 border" aria-sort={ariaSort("example")}>
                            <IconTooltip label="Ordenar por Ejemplo" side="top">
                                <button
                                    type="button"
                                    onClick={() => handleSort("example")}
                                    className={headerBtnCls}
                                    aria-label="Ordenar por Ejemplo"
                                >
                                    Ejemplo {iconForSort("example")}
                                </button>
                            </IconTooltip>
                        </th>

                        <th className="p-2 border" aria-sort={ariaSort("response")}>
                            <IconTooltip label="Ordenar por Respuesta" side="top">
                                <button
                                    type="button"
                                    onClick={() => handleSort("response")}
                                    className={headerBtnCls}
                                    aria-label="Ordenar por Respuesta"
                                >
                                    Respuesta {iconForSort("response")}
                                </button>
                            </IconTooltip>
                        </th>

                        <th className="p-2 border w-36 text-center">Acciones</th>
                    </tr>
                </thead>

                <tbody>
                    {intents.length === 0 ? (
                        <tr>
                            <td colSpan={4} className="text-center p-4 text-gray-500">
                                No hay intents registrados
                            </td>
                        </tr>
                    ) : (
                        intents.map((item, index) => (
                            <tr key={`${item.intent}-${index}`} className="odd:bg-white even:bg-gray-50">
                                <td className="p-2 border align-top font-medium">{item.intent}</td>
                                <td className="p-2 border align-top">{firstExample(item) || "—"}</td>
                                <td className="p-2 border align-top">{firstResponse(item) || "—"}</td>
                                <td className="p-2 border">
                                    <div className="flex items-center justify-center gap-2">
                                        <IconTooltip label="Ver detalles" side="top">
                                            <button
                                                type="button"
                                                onClick={() => handleView(item)}
                                                className="p-1.5 rounded hover:bg-blue-50 text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-300"
                                                aria-label={`Ver detalles de ${item.intent}`}
                                            >
                                                <Eye className="w-5 h-5" />
                                            </button>
                                        </IconTooltip>

                                        <IconTooltip label="Editar intent" side="top">
                                            <button
                                                type="button"
                                                onClick={() => handleEdit(item)}
                                                className="p-1.5 rounded hover:bg-amber-50 text-amber-600 hover:text-amber-800 focus:outline-none focus:ring-2 focus:ring-amber-300"
                                                aria-label={`Editar ${item.intent}`}
                                            >
                                                <Pencil className="w-5 h-5" />
                                            </button>
                                        </IconTooltip>

                                        <IconTooltip label="Eliminar intent" side="top">
                                            <button
                                                type="button"
                                                onClick={() => handleDelete(index, item)}
                                                className="p-1.5 rounded hover:bg-red-50 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-300"
                                                aria-label={`Eliminar ${item.intent}`}
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        </IconTooltip>
                                    </div>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}