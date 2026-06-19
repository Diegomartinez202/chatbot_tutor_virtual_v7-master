// src/pages/BuscarIntentPage.jsx
import React, { useEffect, useState, useMemo } from "react";
import IntentsFilters from "@/components/IntentsFilters";
import IntentsTable from "@/components/IntentsTable";
import Pagination from "@/components/Pagination";
import RefreshButton from "@/components/RefreshButton";
import { fetchIntentsPaged } from "@/services/api";

export default function BuscarIntentPage() {
    const [filters, setFilters] = useState({ q: "", intent: "", example: "", response: "" });
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);

    // ✅ ordenamiento (agregamos setters)
    const [sortBy, setSortBy] = useState(undefined);   // "intent" | "example" | "response"
    const [sortDir, setSortDir] = useState(undefined); // "asc" | "desc"

    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);

    const params = useMemo(
        () => ({
            ...filters,
            page,
            page_size: pageSize,
            sort_by: sortBy,
            sort_dir: sortDir,
        }),
        [filters, page, pageSize, sortBy, sortDir]
    );

    const load = async () => {
        setLoading(true);
        try {
            const { items, total, page: p, page_size } = await fetchIntentsPaged(params);
            setItems(items || []);
            setTotal(total || 0);
            if (p && p !== page) setPage(p);
            if (page_size && page_size !== pageSize) setPageSize(page_size);
        } catch (e) {
            console.error(e);
            setItems([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        // recargar también cuando cambie sort_by / sort_dir
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
        params.page,
        params.page_size,
        params.q,
        params.intent,
        params.example,
        params.response,
        params.sort_by,
        params.sort_dir,
    ]);

    const applyFilters = (f) => {
        setFilters(f);
        setPage(1); // reset de página al filtrar
    };

    return (
        <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Búsqueda de intents</h2>
                <RefreshButton
                    onClick={load}
                    loading={loading}
                    label="Recargar"
                    tooltipLabel="Recargar resultados"
                    variant="outline"
                />
            </div>

            <IntentsFilters initial={filters} onApply={applyFilters} disabled={loading} />

            <div className="rounded-md border bg-white">
                {loading ? (
                    <div className="p-6 text-gray-600">Cargando resultados…</div>
                ) : (
                    <IntentsTable
                        intents={items}
                        // ✅ ordenamiento cableado
                        sortBy={sortBy}
                        sortDir={sortDir}
                        onSortChange={(by, dir) => {
                            setSortBy(by);
                            setSortDir(dir);
                        }}
                    />
                )}

                <div className="px-3">
                    <Pagination
                        page={page}
                        pageSize={pageSize}
                        total={total}
                        onPageChange={setPage}
                        onPageSizeChange={(n) => {
                            setPageSize(n);
                            setPage(1);
                        }}
                        disabled={loading}
                        pageSizeOptions={[10, 20, 50]}
                    />
                </div>
            </div>
        </div>
    );
}