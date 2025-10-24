// src/components/SettingsPanel.jsx
import React, { useEffect, useState } from "react";
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
import i18n from "@/i18n"; // ✅ Importa i18n directamente

const LS_KEY = "app:settings";

const readLS = () => {
    try {
        return JSON.parse(localStorage.getItem(LS_KEY)) || {};
    } catch {
        return {};
    }
};

const writeLS = (obj) => localStorage.setItem(LS_KEY, JSON.stringify(obj));

export default function SettingsPanel({
    open,
    onClose,
    isAuthenticated = false,
    onLogout,
    onCloseChat,
    onLanguageChange,
}) {
    const initial = {
        language: "es",
        darkMode: false,
        fontScale: 1,
        highContrast: false,
        ...readLS(),
    };

    const [state, setState] = useState(initial);

    // ✅ Aplica y guarda configuración visual / idioma
    useEffect(() => {
        document.documentElement.classList.toggle("dark", !!state.darkMode);
        document.documentElement.style.fontSize = `${16 * (state.fontScale || 1)}px`;
        document.documentElement.classList.toggle("high-contrast", !!state.highContrast);

        writeLS(state);

        if (onLanguageChange) onLanguageChange(state.language);
        i18n.changeLanguage(state.language);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [state.darkMode, state.fontScale, state.highContrast, state.language]);

    // ✅ Mantener “Modo oscuro” y “Alto contraste” activos al recargar
    useEffect(() => {
        const saved = readLS();

        if (saved?.darkMode) {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }

        if (saved?.highContrast) {
            document.documentElement.classList.add("high-contrast");
        } else {
            document.documentElement.classList.remove("high-contrast");
        }
    }, []);

    if (!open) return null;

    const fontPct = Math.round((state.fontScale || 1) * 100);

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
                        Configuración
                    </h2>
                    <IconTooltip label="Cerrar panel" side="left">
                        <button
                            onClick={onClose}
                            className="p-2 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800"
                            aria-label="Cerrar"
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
                                <Moon size={16} /> Apariencia
                            </h3>
                            <IconTooltip label="Activa modo oscuro, ajusta el tamaño de fuente.">
                                <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <div className="flex items-center gap-3">
                            <IconTooltip
                                label={state.darkMode ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
                                side="top"
                            >
                                <button
                                    type="button"
                                    onClick={() => setState((s) => ({ ...s, darkMode: !s.darkMode }))}
                                    className={`px-3 py-1.5 text-sm rounded border inline-flex items-center gap-1.5 transition 
                                    ${state.darkMode
                                            ? "bg-zinc-800 text-white hover:bg-zinc-700"
                                            : "bg-white text-zinc-900 hover:bg-zinc-50"}`}
                                    aria-pressed={state.darkMode}
                                    aria-label={state.darkMode ? "Tema claro" : "Tema oscuro"}
                                >
                                    {state.darkMode ? <Sun size={14} /> : <Moon size={14} />}
                                    {state.darkMode ? "Claro" : "Oscuro"}
                                </button>
                            </IconTooltip>

                            <label className="text-sm flex items-center gap-2">
                                <span className="whitespace-nowrap">Tamaño de fuente</span>
                                <IconTooltip label="Ajusta el tamaño de la tipografía de toda la app.">
                                    <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                                </IconTooltip>
                                <input
                                    type="range"
                                    min="0.85"
                                    max="1.3"
                                    step="0.05"
                                    value={state.fontScale}
                                    onChange={(e) =>
                                        setState((s) => ({ ...s, fontScale: Number(e.target.value) }))
                                    }
                                    aria-valuemin={0.85}
                                    aria-valuemax={1.3}
                                    aria-valuenow={state.fontScale}
                                    aria-label="Tamaño de fuente"
                                />
                                <span className="text-xs tabular-nums text-gray-600">{fontPct}%</span>
                            </label>
                        </div>
                    </section>

                    {/* Accesibilidad */}
                    <section className="space-y-2">
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <AccessibilityIcon size={16} /> Accesibilidad
                            </h3>
                            <IconTooltip label="Mejoras de contraste para usuarios con baja visión.">
                                <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <label className="flex items-center gap-2 text-sm">
                            <input
                                type="checkbox"
                                checked={state.highContrast}
                                onChange={(e) =>
                                    setState((s) => ({ ...s, highContrast: e.target.checked }))
                                }
                                aria-checked={state.highContrast}
                                aria-label="Alto contraste"
                            />
                            Alto contraste
                        </label>
                        <p className="text-xs text-zinc-500">
                            Puedes ajustar estilos adicionales en tu CSS global con la clase{" "}
                            <code>html.high-contrast</code>.
                        </p>
                    </section>

                    {/* Idioma */}
                    <section className="space-y-2">
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-medium flex items-center gap-2">
                                <Languages size={16} /> Idioma
                            </h3>
                            <IconTooltip label="Selecciona el idioma de la interfaz.">
                                <Info className="w-3.5 h-3.5 text-gray-500" aria-hidden="true" />
                            </IconTooltip>
                        </div>

                        <select
                            className="border rounded px-3 py-1.5 text-sm bg-white dark:bg-zinc-900"
                            value={state.language}
                            onChange={(e) => {
                                const newLang = e.target.value;
                                setState((s) => ({ ...s, language: newLang }));
                                i18n.changeLanguage(newLang); // ✅ cambio inmediato
                                if (onLanguageChange) onLanguageChange(newLang);
                            }}
                            aria-label="Seleccionar idioma"
                        >
                            <option value="es">🇪🇸 Español</option>
                            <option value="en">🇬🇧 English</option>
                        </select>
                    </section>

                    {/* Sesión / Chat */}
                    <section className="space-y-2">
                        <h3 className="text-sm font-medium">Sesión / Chat</h3>
                        <div className="flex gap-2 flex-wrap">
                            {isAuthenticated ? (
                                <IconTooltip label="Cerrar sesión en la aplicación">
                                    <button
                                        type="button"
                                        onClick={onLogout}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded border bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-white"
                                        aria-label="Cerrar sesión"
                                    >
                                        <LogOut size={14} /> Cerrar sesión
                                    </button>
                                </IconTooltip>
                            ) : (
                                <IconTooltip label="Cerrar el panel/flotante de chat">
                                    <button
                                        type="button"
                                        onClick={onCloseChat}
                                        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded border bg-white hover:bg-zinc-50 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-white"
                                        aria-label="Cerrar chat"
                                    >
                                        <DoorClosed size={14} /> Cerrar chat
                                    </button>
                                </IconTooltip>
                            )}
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}