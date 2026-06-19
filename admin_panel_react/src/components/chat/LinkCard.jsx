import { useEffect, useState } from "react";
import { trackLink } from "@/utils/telemetry"; 

export default function LinkCard({ url }) {
    const [data, setData] = useState(null);

    useEffect(() => {
        let abort = false;
        (async () => {
            try {
                const u = new URL("/api/link/preview", location.origin);
                u.searchParams.set("url", url);
                const res = await fetch(u.toString(), { credentials: "include" });
                if (!res.ok) return;
                const j = await res.json();
                if (!abort) setData(j);
            } catch { }
        })();
        return () => (abort = true);
    }, [url]);

    if (!data) return null;
    return (
        <a
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => trackLink(data.url, { where: "LinkCard" })} // 👈 usa util
            className="block rounded-lg border p-3 hover:shadow"
        >
            {data.image && (
                <img
                    src={data.image}
                    alt=""
                    className="w-full h-40 object-cover rounded mb-2"
                />
            )}
            <div className="font-medium">{data.title || data.url}</div>
            {data.description && (
                <div className="text-sm text-slate-600 line-clamp-3">
                    {data.description}
                </div>
            )}
        </a>
    );
}
