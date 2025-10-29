import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    Settings, LogOut, Sun, Moon, Languages,
    UserPlus, LogIn, Shield, Contrast
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

    const { logout } = useAuth();
    const { t, i18n } = useTranslation("config");   // <-- el hook va DENTRO del componente
    const navigate = useNavigate();

    const zajunaSSO = useMemo(
        () => import.meta.env.VITE_ZAJUNA_SSO_URL || import.meta.env.VITE_ZAJUNA_LOGIN_URL || "",
        []
    );

    // cargar preferencias
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
    }, [i18n]);

    // click outside
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

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        safeSetLS(THEME_KEY, next);
        mergeAppSettings({ darkMode: next === "dark" });
        applyTheme(next);
        window.parent?.postMessage({ type: "prefs:update", prefs: { theme: next } }, "*");
    };

    const changeLang = (val) => {
        setLang(val);
        safeSetLS(LANG_KEY, val);
        i18n.changeLanguage(val);
        mergeAppSettings({ language: val });
        window.parent?.postMessage({ type: "prefs:update", prefs: { language: val } }, "*");
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

    // Redirección a Zajuna SSO en top (sirve en web y widget)
    const goZajuna = () => {
        if (!zajunaSSO) return;
        window.top.location.href = zajunaSSO;
    };

    return (
        <div className={`relative ${className}`}>
            <button
                ref={btnRef}
                type="button"
                onClick={() => setOpen(v => !v)}
                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50"
                aria-haspopup="menu"
                aria-expanded={open ? "true" : "false"}
                aria-label={t("title", "Configuración")}
            >
                <Settings className="w-4 h-4" />
                {t("title", "Configuración")}
            </button>

            {open && (
                <div
                    ref={menuRef}
                    className="absolute right-0 mt-2 w-80 max-w-[90vw] bg-white border shadow-lg rounded-lg p-3 z-50"
                    role="menu"
                >
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">
                            {t("accessibility", "Accesibilidad")}
                        </p>

                        {/* idioma */}
                        <div className="flex justify-between items-center mb-2">
                            <div className="flex items-center gap-2">
                                <Languages className="w-4 h-4 text-gray-600" />
                                <span className="text-sm">{t("language", "Idioma")}</span>
                            </div>
                            <select
                                value={lang}
                                onChange={(e) => changeLang(e.target.value)}
                                className="text-sm border rounded px-2 py-1 bg-white"
                            >
                                <option value="es">Español</option>
                                <option value="en">English</option>
                            </select>
                        </div>

                        {/* tema */}
                        <div className="flex justify-between items-center mb-2">
                            <div className="flex items-center gap-2">
                                {theme === "dark" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                                <span className="text-sm">{t("theme", "Apariencia")}</span>
                            </div>
                            <button
                                type="button"
                                onClick={toggleTheme}
                                className="text-sm border rounded px-2 py-1 bg-white hover:bg-gray-50"
                            >
                                {theme === "dark" ? t("dark", "Oscuro") : t("light", "Claro")}
                            </button>
                        </div>

                        {/* Alto contraste */}
                        <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                                <Contrast className="w-4 h-4" />
                                <span className="text-sm">{t("high_contrast", "Alto contraste")}</span>
                            </div>
                            <button
                                type="button"
                                onClick={toggleContrast}
                                className={`text-sm border rounded px-2 py-1 ${highContrast ? "bg-gray-900 text-white" : "bg-white"} hover:bg-gray-50`}
                            >
                                {highContrast ? t("common.on", "Activado") : t("common.off", "Desactivado")}
                            </button>
                        </div>
                    </div>

                    <hr className="my-2" />

                    {/* panel admin */}
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">
                            {t("adminPanel", "Panel administrativo")}
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <button
                                onClick={() => { navigate("/admin/register"); setOpen(false); }}
                                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <UserPlus className="w-4 h-4" /> {t("registerPanel", "Registrarme (panel)")}
                            </button>
                            <button
                                onClick={() => { navigate("/admin/login"); setOpen(false); }}
                                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <Shield className="w-4 h-4" /> {t("loginPanel", "Iniciar sesión (panel)")}
                            </button>
                        </div>
                    </div>

                    {/* zajuna */}
                    {zajunaSSO && (
                        <>
                            <hr className="my-2" />
                            <p className="text-xs font-semibold text-gray-500 mb-2">{t("zajuna", "Zajuna")}</p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                <button onClick={goZajuna} className="flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm">
                                    <LogIn className="w-4 h-4" /> {t("loginZajuna", "Ingresar con Zajuna")}
                                </button>
                                <button onClick={goZajuna} className="flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm">
                                    <UserPlus className="w-4 h-4" /> {t("registerZajuna", "Registrarse con Zajuna")}
                                </button>
                            </div>
                        </>
                    )}

                    <hr className="my-2" />
                    <div className="flex justify-end">
                        <button
                            onClick={handleLogout}
                            className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                        >
                            <LogOut className="w-4 h-4" /> {t("logout", "Cerrar sesión")}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
