// =====================================================
// 🎧 src/components/voice/VoiceList.jsx
// =====================================================
import { useEffect, useMemo, useState } from "react";

function fmtBytes(bytes) {
    if (!bytes && bytes !== 0) return "";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

async function fetchList({ page = 1, limit = 20, sender, session_id, q } = {}) {
    const u = new URL("/api/voice/list", location.origin);
    u.searchParams.set("page", String(page));
    u.searchParams.set("limit", String(limit));
    if (sender) u.searchParams.set("sender", sender);
    if (session_id) u.searchParams.set("session_id", session_id);
    if (q) u.searchParams.set("q", q);

    const res = await fetch(u.toString(), { credentials: "include" });
    if (!res.ok) throw new Error(`List voice failed: ${res.status}`);
    return res.json();
}

export default function VoiceList({ defaultSender = "", defaultQuery = "" }) {
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(10);
    const [sender, setSender] = useState(defaultSender);
    const [q, setQ] = useState(defaultQuery);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    const pages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [total, limit]);

    useEffect(() => {
        let abort = false;
        async function run() {
            setLoading(true);
            setErr("");
            try {
                const j = await fetchList({ page, limit, sender: sender || undefined, q: q || undefined });
                if (!abort) {
                    setItems(j.items || []);
                    setTotal(Number(j.total || 0));
                }
            } catch (e) {
                if (!abort) setErr(e?.message || "Error cargando audios");
            } finally {
                if (!abort) setLoading(false);
            }
        }
        run();
        return () => { abort = true; };
    }, [page, limit, sender, q]);

    return (
        <div className="space-y-3">
            <div className="flex flex-wrap gap-2 items-end">
                <div className="flex flex-col">
                    <label className="text-sm text-slate-600">Sender</label>
                    <input
                        value={sender}
                        onChange={(e) => setSender(e.target.value)}
                        className="border rounded px-2 py-1"
                        placeholder="web-demo / email / id"
                    />
                </div>
                <div className="flex flex-col">
                    <label className="text-sm text-slate-600">Buscar</label>
                    <input
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        className="border rounded px-2 py-1"
                        placeholder="filename o transcript…"
                    />
                </div>
                <div className="flex flex-col">
                    <label className="text-sm text-slate-600">Por página</label>
                    <select
                        value={limit}
                        onChange={(e) => { setLimit(Number(e.target.value)); setPage(1); }}
                        className="border rounded px-2 py-1"
                    >
                        {[10, 20, 50].map(n => <option key={n} value={n}>{n}</option>)}
                    </select>
                </div>
                <button
                    type="button"
                    onClick={() => setPage(1)}
                    className="ml-auto border rounded px-3 py-1 hover:bg-gray-50"
                    disabled={loading}
                >
                    {loading ? "Cargando…" : "Actualizar"}
                </button>
            </div>

            {err && <div className="text-red-600 text-sm">{err}</div>}

            <div className="overflow-x-auto border rounded">
                <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="text-left px-3 py-2">Archivo</th>
                            <th className="text-left px-3 py-2">Sender</th>
                            <th className="text-left px-3 py-2">Tamaño</th>
                            <th className="text-left px-3 py-2">Transcript</th>
                            <th className="text-left px-3 py-2">Reproducir</th>
                            <th className="text-left px-3 py-2">Descargar</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr><td className="px-3 py-3 text-slate-500" colSpan={6}>Sin resultados</td></tr>
                        ) : items.map(it => (
                            <tr key={it.id} className="border-t">
                                <td className="px-3 py-2">
                                    <div className="font-medium">{it.filename}</div>
                                    <div className="text-xs text-slate-500">{it.mime}</div>
                                </td>
                                <td className="px-3 py-2">{it.sender || "-"}</td>
                                <td className="px-3 py-2">{fmtBytes(it.size)}</td>
                                <td className="px-3 py-2 max-w-[360px]">
                                    <div className="line-clamp-2">{it.transcript || <span className="text-slate-400">—</span>}</div>
                                </td>
                                <td className="px-3 py-2">
                                    {/* Reproducir inline desde /api/media/{id} */}
                                    <audio controls preload="none" src={it.url} className="w-56" />
                                </td>
                                <td className="px-3 py-2">
                                    <a
                                        className="text-indigo-600 underline"
                                        href={it.download_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        Descargar
                                    </a>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="flex items-center justify-between">
                <div className="text-sm text-slate-600">
                    Total: {total} • Página {page} de {pages}
                </div>
                <div className="flex gap-2">
                    <button
                        className="border rounded px-3 py-1 hover:bg-gray-50 disabled:opacity-50"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page <= 1}
                    >
                        ◀
                    </button>
                    <button
                        className="border rounded px-3 py-1 hover:bg-gray-50 disabled:opacity-50"
                        onClick={() => setPage(p => Math.min(pages, p + 1))}
                        disabled={page >= pages}
                    >
                        ▶
                    </button>
                </div>
            </div>
        </div>
    );
}
