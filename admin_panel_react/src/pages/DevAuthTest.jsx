// src/pages/DevAuthTest.jsx
import React, { useState } from "react";
import axiosClient, { setAuthToken } from "@/services/axiosClient";
import { STORAGE_KEYS } from "@/lib/constants";

export default function DevAuthTest() {
    const [out, setOut] = useState("");

    const log = (o) =>
        setOut((prev) => `${prev}\n${typeof o === "string" ? o : JSON.stringify(o, null, 2)}`);

    async function callMe() {
        setOut("");
        try {
            const r = await axiosClient.get("/auth/me");
            log(["/auth/me OK", r.data]);
        } catch (e) {
            log(["/auth/me ERR", e?.response?.status, e?.message]);
        }
    }

    async function callRefresh() {
        try {
            const r = await axiosClient.post("/auth/refresh", {});
            const access = r?.data?.access_token || r?.data?.token;
            log(["/auth/refresh", r.status, !!access]);
            if (access) {
                try { localStorage.setItem(STORAGE_KEYS.accessToken, access); } catch { }
                setAuthToken(access);
                log("Nuevo access_token aplicado a Authorization.");
            }
        } catch (e) {
            log(["/auth/refresh ERR", e?.response?.status, e?.message]);
        }
    }

    async function dropToken() {
        try { localStorage.removeItem(STORAGE_KEYS.accessToken); } catch { }
        setAuthToken(null);
        log("Authorization limpio; siguiente /auth/me debe 401.");
    }

    async function logout() {
        try { await axiosClient.post("/auth/logout"); } catch { }
        try { localStorage.removeItem(STORAGE_KEYS.accessToken); } catch { }
        setAuthToken(null);
        log("Logout: cookie de refresh borrada y header limpio.");
    }

    // ⬇️ Botón pedido: fuerza 401 y deja que el interceptor pruebe /auth/refresh
    async function force401ThenTryRefresh() {
        setOut("");
        try { localStorage.removeItem(STORAGE_KEYS.accessToken); } catch { }
        setAuthToken(null);
        log("Authorization removido → ahora /auth/me devolverá 401…");

        try {
            const r = await axiosClient.get("/auth/me");
            log(["/auth/me luego del 401 (si refresh funcionó, debería estar OK)", r?.data]);
        } catch (e) {
            log(["/auth/me tras intento de refresh ERR", e?.response?.status, e?.message]);
        }
    }

    return (
        <div className="p-6 max-w-3xl mx-auto">
            <h1 className="text-xl font-semibold mb-3">Dev Auth Test</h1>
            <div className="grid grid-cols-2 gap-3 mb-4">
                <button className="px-3 py-2 border rounded" onClick={callMe}>GET /auth/me</button>
                <button className="px-3 py-2 border rounded" onClick={callRefresh}>POST /auth/refresh</button>
                <button className="px-3 py-2 border rounded" onClick={dropToken}>Quitar Authorization</button>
                <button className="px-3 py-2 border rounded" onClick={logout}>Logout (borra cookie)</button>

                {/* Nuevo: Forzar 401 y probar refresh automático del interceptor */}
                <button className="px-3 py-2 border rounded col-span-2" onClick={force401ThenTryRefresh}>
                    Forzar 401 + probar refresh
                </button>
            </div>
            <pre className="bg-black text-green-300 p-3 rounded min-h-[220px] overflow-auto whitespace-pre-wrap">
                {out || "Listo para probar. 1) /auth/me  2) /auth/refresh  3) Forzar 401 + probar refresh…"}
            </pre>
        </div>
    );
}
