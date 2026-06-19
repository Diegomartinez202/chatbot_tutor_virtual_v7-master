// src/components/IntentsFilters.jsx
import React, { useState, useEffect } from "react";
import { Search, FilterX, Eraser } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import { Button } from "@/components/ui/button";

export default function IntentsFilters({
    initial = { q: "", intent: "", example: "", response: "" },
    onApply,
    disabled = false,
}) {
    const [q, setQ] = useState(initial.q || "");
    const [intent, setIntent] = useState(initial.intent || "");
    const [example, setExample] = useState(initial.example || "");
    const [response, setResponse] = useState(initial.response || "");

    useEffect(() => {
        setQ(initial.q || "");
        setIntent(initial.intent || "");
        setExample(initial.example || "");
        setResponse(initial.response || "");
    }, [initial]);

    const apply = (e) => {
        e?.preventDefault?.();
        onApply?.({ q: q.trim(), intent: intent.trim(), example: example.trim(), response: response.trim() });
    };

    const clear = () => {
        setQ(""); setIntent(""); setExample(""); setResponse("");
        onApply?.({ q: "", intent: "", example: "", response: "" });
    };

    return (
        <form onSubmit={apply} className="grid grid-cols-1 md:grid-cols-5 gap-2 bg-white border rounded-md p-3">
            <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Búsqueda libre</label>
                <div className="flex items-center gap-2">
                    <input
                        className="w-full border rounded-md px-3 py-2 text-sm"
                        placeholder="texto en intent/ejemplos/respuestas…"
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        disabled={disabled}
                        aria-label="Buscar"
                    />
                    <IconTooltip label="Buscar">
                        <button type="submit" className="p-2 rounded border hover:bg-gray-50" disabled={disabled} aria-label="Buscar">
                            <Search className="w-4 h-4" />
                        </button>
                    </IconTooltip>
                </div>
            </div>

            <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Intent</label>
                <input
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    placeholder="saludo"
                    value={intent}
                    onChange={(e) => setIntent(e.target.value)}
                    disabled={disabled}
                />
            </div>

            <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Ejemplo</label>
                <input
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    placeholder="hola"
                    value={example}
                    onChange={(e) => setExample(e.target.value)}
                    disabled={disabled}
                />
            </div>

            <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Respuesta</label>
                <input
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    placeholder="¡Hola!"
                    value={response}
                    onChange={(e) => setResponse(e.target.value)}
                    disabled={disabled}
                />
            </div>

            <div className="md:col-span-5 flex items-center justify-end gap-2">
                <IconTooltip label="Aplicar filtros">
                    <Button type="submit" disabled={disabled} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                        <FilterX className="w-4 h-4 mr-2" />
                        Filtrar
                    </Button>
                </IconTooltip>

                <IconTooltip label="Limpiar filtros">
                    <Button type="button" variant="outline" onClick={clear} disabled={disabled}>
                        <Eraser className="w-4 h-4 mr-2" />
                        Limpiar
                    </Button>
                </IconTooltip>
            </div>
        </form>
    );
}