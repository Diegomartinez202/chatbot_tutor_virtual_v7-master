import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    Settings, LogOut, Sun, Moon, Languages, UserPlus, LogIn, Shield, Contrast
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";

const THEME_KEY = "chat.theme";
const LANG_KEY = "chat.lang";
const CONTRAST_KEY = "chat.high_contrast";
const APP_SETTINGS_KEY = "app:settings";

function applyTheme(theme) {
    const html = document.documentElement;
    html.classList.toggle("dark", theme === "dark");
}
function applyHighContrast(on) {
    const html = document.documentElement;
    html.classList.toggle("high-contrast", !!on);
}
function safeGetLS(k, f) { try { return localStorage.getItem(k) ?? f; } catch { return f; } }
function safeSetLS(k, v) { try { localStorage.setItem(k, v); } catch { } }
function mergeAppSettings(patch) {
    try {
        const raw = localStorage.getItem(APP_SETTINGS_KEY);
        const cur = raw ? JSON.parse(raw) : {};
        localStorage.setItem(APP_SETTINGS_KEY, JSON.stringify({ ...cur, ...patch }));
    } catch { }
}

export default function ChatConfigMenu({ className = "" }) {
    const [open, setOpen] = useState(false);
    const [theme, setTheme] = useState("light");
    const [lang, setLang] = useState("es");
    const [highContrast, setHighContrast] = useState(false);
    const btnRef = useRef(null);
    const menuRef = useRef(null);

    const { isAuthenticated, logout, redirectToZajunaSSO } = useAuth();
    const { i18n } = useTranslation();
    const navigate = useNavigate();

    // URL SSO Zajuna (si existe en .env)
    const zajunaSSO = useMemo(
        () => (import.meta.env.VITE_ZAJUNA_SSO_URL || import.meta.env.VITE_ZAJUNA_LOGIN_URL || "").trim(),
        []
    );

    /* ------- Estado inicial desde localStorage ------- */
    useEffect(() => {
        const savedTheme =
            safeGetLS(THEME_KEY, null) ||
            (JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.darkMode ? "dark" : "light");

        const savedLang =
            safeGetLS(LANG_KEY, null) ||
            JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.language ||
            "es";

        const savedContrast = safeGetLS(CONTRAST_KEY, "0") === "1";

        setTheme(savedTheme);
        setLang(savedLang);
        setHighContrast(savedContrast);

        applyTheme(savedTheme);
        applyHighContrast(savedContrast);
        i18n.changeLanguage(savedLang);
        document.documentElement.setAttribute("lang", savedLang === "en" ? "en" : "es");
    }, [i18n]);

    /* ------- Cerrar al hacer click fuera / ESC ------- */
    useEffect(() => {
        if (!open) return;
        const onDocClick = (e) => {
            if (menuRef.current?.contains(e.target)) return;
            if (btnRef.current?.contains(e.target)) return;
            setOpen(false);
        };
        const onEsc = (e) => e.key === "Escape" && setOpen(false);
        document.addEventListener("mousedown", onDocClick);
        document.addEventListener("keydown", onEsc);
        return () => {
            document.removeEventListener("mousedown", onDocClick);
            document.removeEventListener("keydown", onEsc);
        };
    }, [open]);

    /* ------- Acciones ------- */
    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        safeSetLS(THEME_KEY, next);
        mergeAppSettings({ darkMode: next === "dark" });
        applyTheme(next);
        window.parent?.postMessage({ type: "prefs:update", prefs: { theme: next } }, "*");
    };

    const changeLang = (val) => {
        const lang = val === "en" ? "en" : "es";
        setLang(lang);
        safeSetLS(LANG_KEY, lang);
        i18n.changeLanguage(lang);
        mergeAppSettings({ language: lang });
        document.documentElement.setAttribute("lang", lang);
        window.parent?.postMessage({ type: "prefs:update", prefs: { language: lang } }, "*");
    };

    const toggleContrast = () => {
        const next = !highContrast;
        setHighContrast(next);
        safeSetLS(CONTRAST_KEY, next ? "1" : "0");
        applyHighContrast(next);
        mergeAppSettings({ highContrast: next });
        window.parent?.postMessage({ type: "prefs:update", prefs: { highContrast: next } }, "*");
    };

    const handleLogout = async () => {
        try { await logout?.(); } catch { }
        navigate("/", { replace: true });
    };

    // Login con Zajuna
    const goZajuna = () => {
        if (typeof redirectToZajunaSSO === "function") return redirectToZajunaSSO();
        if (!zajunaSSO) return;
        if (window.self !== window.top) window.top.location.href = zajunaSSO;
        else window.location.href = zajunaSSO;
    };

    // Login/Registro local (app)
    const goLoginApp = () => navigate("/login");
    const goRegisterApp = () => navigate("/register");

    const langLabel = lang === "en" ? "English" : "Español";
    const themeLabel = theme === "dark" ? "Oscuro" : "Claro";
    const contrastLabel = highContrast ? "Alto contraste: ON" : "Alto contraste: OFF";

    return (
        <div className={`relative ${className}`}>
            <button
                type="button"
                ref={btnRef}
                onClick={() => setOpen(v => !v)}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border text-sm bg-white hover:bg-gray-50"
                aria-haspopup="menu"
                aria-expanded={open}
            >
                <Settings className="w-4 h-4" />
                Configuración
            </button>

            {open && (
                <div
                    ref={menuRef}
                    role="menu"
                    className="absolute right-0 mt-2 w-64 bg-white border rounded-xl shadow-xl p-1 z-50"
                >
                    {/* === Panel administrativo / Zajuna === */}
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        Panel administrativo
                    </div>

                    <button
                        role="menuitem"
                        onClick={goZajuna}
                        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded"
                    >
                        <Shield className="w-4 h-4" />
                        Iniciar sesión / Registrarse con Zajuna
                    </button>

                    <div className="my-1 h-px bg-gray-200" />

                    {/* === Preferencias de visualización === */}
                    <button
                        role="menuitem"
                        onClick={toggleTheme}
                        className="w-full flex items-center justify-between gap-2 px-3 py-2 hover:bg-gray-100 rounded"
                    >
                        <span className="flex items-center gap-2">
                            {theme === "dark" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                            Tema
                        </span>
                        <span className="text-xs text-gray-500">{themeLabel}</span>
                    </button>

                    <button
                        role="menuitem"
                        onClick={toggleContrast}
                        className="w-full flex items-center justify-between gap-2 px-3 py-2 hover:bg-gray-100 rounded"
                    >
                        <span className="flex items-center gap-2">
                            <Contrast className="w-4 h-4" />
                            Accesibilidad
                        </span>
                        <span className="text-xs text-gray-500">{contrastLabel}</span>
                    </button>

                    <div className="flex items-center justify-between gap-2 px-3 py-2">
                        <span className="flex items-center gap-2 text-sm">
                            <Languages className="w-4 h-4" />
                            Idioma
                        </span>
                        <div className="flex gap-1">
                            <button
                                type="button"
                                aria-label="Cambiar a Español"
                                onClick={() => changeLang("es")}
                                className={`px-2 py-1 text-xs rounded border ${lang === "es" ? "bg-indigo-600 text-white border-indigo-600" : "bg-white hover:bg-gray-100"}`}
                            >
                                ES
                            </button>
                            <button
                                type="button"
                                aria-label="Switch to English"
                                onClick={() => changeLang("en")}
                                className={`px-2 py-1 text-xs rounded border ${lang === "en" ? "bg-indigo-600 text-white border-indigo-600" : "bg-white hover:bg-gray-100"}`}
                            >
                                EN
                            </button>
                        </div>
                    </div>

                    <div className="px-3 pb-2 text-xs text-gray-500">Actual: {langLabel}</div>

                    <div className="my-1 h-px bg-gray-200" />

                    {/* === Sesión local de la app === */}
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        Sesión (aplicación)
                    </div>

                    <button
                        role="menuitem"
                        onClick={goLoginApp}
                        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded"
                    >
                        <LogIn className="w-4 h-4" />
                        Iniciar sesión (app)
                    </button>

                    <button
                        role="menuitem"
                        onClick={goRegisterApp}
                        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded"
                    >
                        <UserPlus className="w-4 h-4" />
                        Registrarse (app)
                    </button>

                    {isAuthenticated && (
                        <>
                            <div className="my-1 h-px bg-gray-200" />
                            <button
                                role="menuitem"
                                onClick={handleLogout}
                                className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded text-red-600"
                            >
                                <LogOut className="w-4 h-4" />
                                Cerrar sesión
                            </button>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
