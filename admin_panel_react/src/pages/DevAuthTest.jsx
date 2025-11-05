// src/pages/DevAuthTest.jsx
import React, { useState } from "react";
import axiosClient, { setAuthToken } from "@/services/axiosClient";
import { STORAGE_KEYS } from "@/lib/constants";

export default function DevAuthTest() {
    const [log, setLog] = useState([]);

    const push = (m) => setLog((x) => [...x, m]);

    const callMe = async () => {
        try {
            const r = await axiosClient.get("/auth/me");
            push({ ok: true, where: "/auth/me", data: r.data });
        } catch (e) {
            push({ ok: false, where: "/auth/me", error: e?.message || "err" });
        }
    };

    const breakAccess = async () => {
        try {
            localStorage.setItem(STORAGE_KEYS.accessToken, "xxx.invalid.token");
            setAuthToken("xxx.invalid.token");
            push({ ok: true, where: "breakAccess", data: "header cambiado a token inválido" });
        } catch { }
    };

    const refresh = async () => {
        try {
            const r = await axiosClient.post("/auth/refresh");
            push({ ok: true, where: "/auth/refresh", data: r.data });
        } catch (e) {
            push({ ok: false, where: "/auth/refresh", error: e?.message || "err" });
        }
    };

    const logout = async () => {
        try {
            await axiosClient.post("/auth/logout");
        } catch { }
        try { localStorage.removeItem(STORAGE_KEYS.accessToken); } catch { }
        setAuthToken(null);
        push({ ok: true, where: "logout", data: "cookie borrada y header limpio" });
    };

    return (
        <div className="p-4 space-y-3">
            <div className="flex gap-2">
                <button onClick={callMe} className="px-3 py-1 border rounded">/auth/me</button>
                <button onClick={breakAccess} className="px-3 py-1 border rounded">Romper access</button>
                <button onClick={refresh} className="px-3 py-1 border rounded">/auth/refresh</button>
                <button onClick={logout} className="px-3 py-1 border rounded">Logout</button>
            </div>
            <pre className="text-xs bg-gray-50 p-3 rounded">{JSON.stringify(log, null, 2)}</pre>
        </div>
    );
}
