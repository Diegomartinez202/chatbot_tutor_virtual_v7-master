// src/components/SettingsPanel.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
    X,
    Moon,
    Sun,
    Languages,
    Accessibility as AccessibilityIcon,
    LogOut,
    DoorClosed,
    Info,
} from "lucide-react";
import IconTooltip from "@/components/ui/IconTooltip";
import i18n from "@/i18n";
import { useTranslation } from "react-i18next";
import { toast } from "react-hot-toast"; // 🆕 toaster
import { STORAGE_KEYS } from "@/lib/constants";

// ===== Token helper (sin romper SSR/tests) =====
function getAccessTokenSafe() {
    try {
        // 1) Si tu app expone en memoria (ej. Zustand): window.__APP_ACCESS_TOKEN__
        if (typeof window !== "undefined" && window.__APP_ACCESS_TOKEN__) {
            return String(window.__APP_ACCESS_TOKEN__);
        }
        // 2) Fallback a localStorage
        if (typeof window !== "undefined") {
            return (
                window.localStorage.getItem(STORAGE_KEYS.accessToken) ||
                window.localStorage.getItem("zajuna_token") ||
                null
            );
        }
    } catch { /* ignore */ }
    return null;
}

const LS_KEY = "app:settings";

/** Lee settings locales sin romper SSR/tests */
const safeReadLS = () => {
    try {
        if (typeof window === "undefined") return {};
        const raw = window.localStorage.getItem(LS_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch {
        return {};
    }
};

const writeLS = (obj) => {
    try {
        if (typeof window === "undefined") return;
        window.localStorage.setItem(LS_KEY, JSON.stringify(obj));
    } catch {
        /* ignore */
    }
};

/** (Opcional) sincronizar preferencia con backend
 *  - No se ejecuta si no defines VITE_USER_SETTINGS_URL
 *  - Retorna { ok: boolean, status?: number, skipped?: boolean }
 */
async function maybeSyncToBackend(prefs) {
    const url = import.meta.env.VITE_USER_SETTINGS_URL; // ej: /api/me/settings
    if (!url) return { ok: false, skipped: true }; // ❌ sin endpoint → no hace nada

    try {
        const token = getAccessTokenSafe();
        const headers = { "Content-Type": "application/json" };
        if (token) headers.Authorization = `Bearer ${token}`;

        const res = await fetch(url, {
            method: "PUT",
            headers,
            // ✅ ahora por header Authorization (no cookies httpOnly)
            body: JSON.stringify({
                language: prefs.language,
                theme: prefs.darkMode ? "dark" : "light",
                fontScale: prefs.fontScale,
                highContrast: !!prefs.highContrast,
            }),
        });

        const data = await res.json().catch(() => null);
        const ok = res.ok && (data?.ok ?? true);
        return { ok, status: res.status };
    } catch {
        // Silencioso: no rompemos UX si el backend no está listo
        return { ok: false };
    }
}

/** (Nuevo) GET inicial para precargar preferencias remotas.
 *    - Si no hay endpoint, se omite.
 *    - Si 200, aplicamos al panel y a localStorage sin romper local.
 */
async function maybeFetchPrefsFromBackend() {
    const url = import.meta.env.VITE_USER_SETTINGS_URL;
    if (!url) return { ok: false, skipped: true };

    try {
        const token = getAccessTokenSafe();
        const headers = {};
        if (token) headers.Authorization = `Bearer ${token}`;

        const res = await fetch(url, { method: "GET", headers });
        if (!res.ok) return { ok: false, status: res.status };

        const data = await res.json().catch(() => ({}));
        const prefs = {
            language: data.language ?? "es",
            darkMode: (data.theme ?? "light") === "dark",
            fontScale: typeof data.fontScale === "number" ? data.fontScale : 1,
            highContrast: !!data.highContrast,
        };
        return { ok: true, prefs };
    } catch {
        return { ok: false };
    }
}

export default function SettingsPanel({
    open,
    onClose,
    isAuthenticated = false,
    onLogout,
    onCloseChat,
    onLanguageChange,
}) {
    // i18n namespaces: textos del panel en 'config', textos comunes en defaultNS ('common')
    const { t: tConfig } = useTranslation("config");
    const { t } = useTranslation(); // defaultNS=common (logout, etc.)

    const initial = useMemo(
        () => ({
            language: "es",
            darkMode: false,
            fontScale: 1,
            highContrast: false,
            ...safeReadLS(),
        }),
        []
    );

    const [state, setState] = useState(initial);
    const [loadedRemote, setLoadedRemote] = useState(false);

    // 🆕 debounce para no mostrar múltiples toasts si el usuario mueve el slider
    const toastTimerRef = useRef(null);
    const scheduleToast = () => {
        if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
        toastTimerRef.current = setTimeout(() => {
            toast.success(tConfig("prefs_synced", "Preferencias sincronizadas"));
            toastTimerRef.current = null;
        }, 450);
    };

    // 🆕 GET inicial (una sola vez cuando se abra el panel por primera vez)
    useEffect(() => {
        let alive = true;
        if (!open || loadedRemote) return;

        (async () => {
            const res = await maybeFetchPrefsFromBackend();
            if (!alive) return;

            if (res.ok && res.prefs) {
                // Actualiza estado y persistencia local sin romper tus defaults
                const merged = { ...state, ...res.prefs };
                setState(merged);
                writeLS(merged);

                // Aplica i18n inmediatamente si vino language
                if (merged.language) {
                    i18n.changeLanguage(merged.language);
                    onLanguageChange?.(merged.language);
                }
            }
            setLoadedRemote(true);
        })();

        return () => { alive = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open]);

    // Aplicar tema/escala/contraste + persistir + cambiar idioma + sync backend (opcional)
    useEffect(() => {
        const html = document.documentElement;

        // Tema
        html.classList.toggle("dark", !!state.darkMode);

        // Tamaño base de fuente
        const scale = Number(state.fontScale || 1);
        html.style.fontSize = `${16 * scale}px`;

        // Alto contraste
        html.classList.toggle("high-contrast", !!state.highContrast);

        // Guardar local
        writeLS(state);

        // Idioma
        if (state.language) {
            i18n.changeLanguage(state.language);
            onLanguageChange?.(state.language);
        }

        // (Opcional) sincronizar con backend si configuraste la URL
        (async () => {
            const result = await maybeSyncToBackend(state);
            // Mostrar toaster sólo si hubo backend y respondió OK
            if (result.ok && !result.skipped) {
                scheduleToast();
            }
        })();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [state.darkMode, state.fontScale, state.highContrast, state.language]);

    // Reaplicar clases en primer montaje (por si recarga)
    useEffect(() => {
        const saved = safeReadLS();
        const html = document.documentElement;
        if (saved?.darkMode) html.classList.add("dark");
        if (saved?.highContrast) html.classList.add("high-contrast");
    }, []);

    if (!open) return null;

    const fontPct = Math.round((Number(state.fontScale) || 1) * 100);

    return (
        <div className="fixed inset-0 z-[9999]">
            {/* overlay */}
            <div
                className="absolute inset-0 bg-black/30"
                onClick={onClose}
                aria-hidden="true"
            />
            {/* panel */}
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="settings-title"
                className="absolute right-0 top-0 h-full w-full sm:w-[420px] bg-white dark:bg-zinc-900 shadow-2xl border-l border-zinc-200 dark:border-zinc-800 flex flex-col"
            >
                <div className="flex items-center justify-between p-4 border-b border-zinc-200 dark:border-zinc-800">
                    <h2 id="settings-title" className="text-lg font-semibold">
                        {tConfig("title")}
                    </h2>
                    <IconTooltip label={t("close")} side="left">
                        <button
                            onClick={onClose}
                            className="p-2 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800"
                            aria-label={t("close")}
                            type="button"
                        >
                            <X size={18} />
                        </button>
                    </IconTooltip>
                </div>

                <div className="p-4 space-y-6 overflow-auto">
                    {/* Apariencia */}
                    <section className="space-y-2">
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <Moon size={16} /> {tConfig("theme")}
                            </h3>
                            <IconTooltip label={tConfig("theme_help", "Ajusta el tema y el tamaño de fuente")}>
                                <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <div className="flex items-center gap-3">
                            <IconTooltip
                                label={state.darkMode ? tConfig("light") : tConfig("dark")}
                                side="top"
                            >
                                <button
                                    type="button"
                                    onClick={() => setState((s) => ({ ...s, darkMode: !s.darkMode }))}
                                    className={`px-3 py-1.5 text-sm rounded border inline-flex items-center gap-1.5 transition 
                    ${state.darkMode
                                            ? "bg-zinc-800 text-white hover:bg-zinc-700"
                                            : "bg-white text-zinc-900 hover:bg-zinc-50"
                                        }`}
                                    aria-pressed={state.darkMode}
                                    aria-label={state.darkMode ? tConfig("light") : tConfig("dark")}
                                >
                                    {state.darkMode ? <Sun size={14} /> : <Moon size={14} />}
                                    {state.darkMode ? tConfig("light") : tConfig("dark")}
                                </button>
                            </IconTooltip>

                            <label className="text-sm flex items-center gap-2">
                                <span className="whitespace-nowrap">{tConfig("font_size", "Tamaño de fuente")}</span>
                                <IconTooltip label={tConfig("font_size_help", "Ajusta el tamaño de la tipografía de toda la app.")}>
                                    <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                                </IconTooltip>
                                <input
                                    type="range"
                                    min="0.85"
                                    max="1.3"
                                    step="0.05"
                                    value={state.fontScale}
                                    onChange={(e) =>
                                        setState((s) => ({
                                            ...s,
                                            fontScale: Number(e.target.value),
                                        }))
                                    }
                                    aria-valuemin={0.85}
                                    aria-valuemax={1.3}
                                    aria-valuenow={Number(state.fontScale) || 1}
                                    aria-label={tConfig("font_size", "Tamaño de fuente")}
                                />
                                <span className="text-xs tabular-nums text-gray-600">
                                    {fontPct}%
                                </span>
                            </label>
                        </div>
                    </section>

                    {/* Accesibilidad */}
                    <section className="space-y-2">
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <AccessibilityIcon size={16} /> {tConfig("accessibility")}
                            </h3>
                            <IconTooltip label={tConfig("high_contrast_help", "Mejora el contraste para baja visión.")}>
                                <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={!!state.highContrast}
                                onChange={(e) =>
                                    setState((s) => ({ ...s, highContrast: e.target.checked }))
                                }
                                aria-checked={!!state.highContrast}
                                aria-label={tConfig("high_contrast", "Alto contraste")}
                            />
                            {tConfig("high_contrast", "Alto contraste")}
                        </label>
                        <p className="text-xs text-zinc-500">
                            {tConfig(
                                "high_contrast_hint",
                                "Puedes ajustar estilos adicionales en tu CSS global con la clase html.high-contrast."
                            )}
                        </p>
                    </section>

                    {/* Idioma */}
                    <section className="space-y-2">
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <Languages size={16} /> {tConfig("language")}
                            </h3>
                            <IconTooltip label={tConfig("language_help", "Selecciona el idioma de la interfaz.")}>
                                <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <select
                            className="border rounded px-3 py-1.5 text-sm bg-white dark:bg-zinc-900"
                            value={state.language}
                            onChange={(e) => {
                                const newLang = e.target.value;
                                setState((s) => ({ ...s, language: newLang }));
                                i18n.changeLanguage(newLang); // cambio inmediato
                                onLanguageChange?.(newLang);
                            }}
                            aria-label={tConfig("language")}
                        >
                            <option value="es">🇪🇸 Español</option>
                            <option value="en">🇬🇧 English</option>
                        </select>
                    </section>

                    {/* Sesión / Chat */}
                    <section className="space-y-2">
                        <h3 className="text-sm font-medium">{tConfig("session_chat", "Sesión / Chat")}</h3>
                        <div className="flex flex-col sm:flex-row sm:items-center gap-2 flex-wrap">
                            {isAuthenticated ? (
                                <IconTooltip label={tConfig("logout_app", "Cerrar sesión en la aplicación")}>
                                    <button
                                        type="button"
                                        onClick={onLogout}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded border bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-white"
                                        aria-label={t("logout")}
                                    >
                                        <LogOut size={14} /> {t("logout")}
                                    </button>
                                </IconTooltip>
                            ) : (
                                <IconTooltip label={tConfig("close_chat", "Cerrar el panel/flotante de chat")}>
                                    <button
                                        type="button"
                                        onClick={onCloseChat}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded border bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-white"
                                        aria-label={t("close_chat")}
                                    >
                                        <DoorClosed size={14} /> {t("close_chat")}
                                    </button>
                                </IconTooltip>
                            )}
                            {/* Indicador de tema actual */}
                            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-300">
                                {state.highContrast ? (
                                    <span title={tConfig("high_contrast")}>⚡ {tConfig("high_contrast")}</span>
                                ) : state.darkMode ? (
                                    <span title={tConfig("dark")}>🌙 {tConfig("dark")}</span>
                                ) : (
                                    <span title={tConfig("light")}>☀️ {tConfig("light")}</span>
                                )}
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
