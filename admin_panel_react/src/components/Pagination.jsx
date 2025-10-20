// src/components/Pagination.jsx
import React from "react";
import { ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight } from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";

export default function Pagination({
    page = 1,
    pageSize = 10,
    total = 0,
    onPageChange,
    onPageSizeChange,
    pageSizeOptions = [10, 20, 50],
    disabled = false,
}) {
    const totalPages = Math.max(1, Math.ceil((total || 0) / (pageSize || 1)));

    const go = (p) => {
        const np = Math.min(totalPages, Math.max(1, p));
        if (np !== page) onPageChange?.(np);
    };

    return (
        <div className="flex items-center justify-between gap-3 py-3">
            <div className="text-sm text-gray-600">
                Mostrando {(total === 0) ? 0 : ((page - 1) * pageSize + 1)}–{Math.min(page * pageSize, total)} de {total}
            </div>

            <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">Por página:</label>
                <select
                    className="border rounded-md px-2 py-1 text-sm"
                    value={pageSize}
                    onChange={(e) => onPageSizeChange?.(Number(e.target.value))}
                    disabled={disabled}
                    aria-label="Tamaño de página"
                >
                    {pageSizeOptions.map((n) => (
                        <option key={n} value={n}>{n}</option>
                    ))}
                </select>

                <div className="ml-2 flex items-center gap-1">
                    <IconTooltip label="Primera página">
                        <button className="p-1.5 rounded border hover:bg-gray-50" onClick={() => go(1)} disabled={disabled || page <= 1} aria-label="Primera página">
                            <ChevronsLeft className="w-4 h-4" />
                        </button>
                    </IconTooltip>
                    <IconTooltip label="Anterior">
                        <button className="p-1.5 rounded border hover:bg-gray-50" onClick={() => go(page - 1)} disabled={disabled || page <= 1} aria-label="Página anterior">
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                    </IconTooltip>
                    <IconTooltip label="Siguiente">
                        <button className="p-1.5 rounded border hover:bg-gray-50" onClick={() => go(page + 1)} disabled={disabled || page >= totalPages} aria-label="Página siguiente">
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </IconTooltip>
                    <IconTooltip label="Última página">
                        <button className="p-1.5 rounded border hover:bg-gray-50" onClick={() => go(totalPages)} disabled={disabled || page >= totalPages} aria-label="Última página">
                            <ChevronsRight className="w-4 h-4" />
                        </button>
                    </IconTooltip>
                </div>
            </div>
        </div>
    );
}