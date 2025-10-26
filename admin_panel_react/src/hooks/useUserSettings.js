// admin_panel_react/src/hooks/useUserSettings.js
import { useCallback, useEffect, useState } from "react";
import { STORAGE_KEYS } from "@/lib/constants";

/** Obtiene el token desde store/localStorage si existe */
function getAuthToken() {
    try {
        // 1) Store/Zustand/Redux si lo tienes expuesto globalmente (puedes importar getAccessToken si lo usas)
        const fromLs = localStorage.getItem(STORAGE_KEYS.accessToken);
        return fromLs || null;
    } catch {
        return null;
    }
}

const DEFAULT_PREFS = {
    language: "es",
    theme: "light",
    fontScale: 1.0,
    highContrast: false,
};

/** Construye headers con token si existe */
function buildHeaders() {
    const token = getAuthToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
}

export function useUserSettings({ autoLoad = true } = {}) {
    const [prefs, setPrefs] = useState(DEFAULT_PREFS);
    const [loading, setLoading] = useState(autoLoad);
    const [error, setError] = useState(null);

    const URL = import.meta.env.VITE_USER_SETTINGS_URL || "/api/me/settings";

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(URL, {
                method: "GET",
                headers: buildHeaders(),
                credentials: "include",
            });
            if (!res.ok) throw new Error(`GET ${res.status}`);
            const data = await res.json();
            setPrefs({
                language: data.language ?? "es",
                theme: data.theme ?? "light",
                fontScale: Number(data.fontScale ?? 1.0),
                highContrast: !!data.highContrast,
            });
            return data;
        } catch (e) {
            setError(e);
            return null;
        } finally {
            setLoading(false);
        }
    }, [URL]);

    const save = useCallback(async (nextPrefs) => {
        setError(null);
        try {
            const res = await fetch(URL, {
                method: "PUT",
                headers: buildHeaders(),
                credentials: "include",
                body: JSON.stringify({
                    language: nextPrefs.language ?? prefs.language,
                    theme: (nextPrefs.darkMode ?? (prefs.theme === "dark")) ? "dark" : "light",
                    fontScale: Number(nextPrefs.fontScale ?? prefs.fontScale),
                    highContrast: !!(nextPrefs.highContrast ?? prefs.highContrast),
                }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(`PUT ${res.status}`);

            // Normaliza respuesta
            const merged = {
                language: data?.prefs?.language ?? nextPrefs.language ?? prefs.language,
                theme: data?.prefs?.theme ?? ((nextPrefs.darkMode ?? (prefs.theme === "dark")) ? "dark" : "light"),
                fontScale: Number(data?.prefs?.fontScale ?? nextPrefs.fontScale ?? prefs.fontScale),
                highContrast: !!(data?.prefs?.highContrast ?? nextPrefs.highContrast ?? prefs.highContrast),
            };
            setPrefs(merged);
            return { ok: data?.ok ?? res.ok, prefs: merged };
        } catch (e) {
            setError(e);
            return { ok: false, error: e };
        }
    }, [URL, prefs]);

    useEffect(() => {
        if (autoLoad) load();
    }, [autoLoad, load]);

    return { prefs, setPrefs, loading, error, load, save };
}

export default useUserSettings;
