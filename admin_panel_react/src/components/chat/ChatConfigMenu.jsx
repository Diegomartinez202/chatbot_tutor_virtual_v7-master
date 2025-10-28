import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
    Settings,
    LogOut,
    Sun,
    Moon,
    Languages,
    UserPlus,
    LogIn,
    Shield,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";

const THEME_KEY = "chat.theme";
const LANG_KEY = "chat.lang";

// 👇 para converger con SettingsPanel (sin romper tus claves actuales)
const APP_SETTINGS_KEY = "app:settings";

function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === "dark") html.classList.add("dark");
    else html.classList.remove("dark");
}

function safeGetLS(key, fallback) {
    try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; }
}
function safeSetLS(key, value) {
    try { localStorage.setItem(key, value); } catch { }
}
function mergeAppSettings(patch) {
    try {
        const raw = localStorage.getItem(APP_SETTINGS_KEY);
        const cur = raw ? JSON.parse(raw) : {};
        const next = { ...cur, ...patch };
        localStorage.setItem(APP_SETTINGS_KEY, JSON.stringify(next));
    } catch { }
}

export default function ChatConfigMenu({ className = "" }) {
    const [open, setOpen] = useState(false);
    const [theme, setTheme] = useState("light");
    const [lang, setLang] = useState("es");

    const menuRef = useRef(null);
    const btnRef = useRef(null);

    const navigate = useNavigate();
    const { logout } = useAuth();
    const { t, i18n } = useTranslation();

    const zajunaSSO = useMemo(
        () => import.meta.env.VITE_ZAJUNA_SSO_URL || import.meta.env.VITE_ZAJUNA_LOGIN_URL || "",
        []
    );

    // Cargar preferencias guardadas y aplicarlas (incluye app:settings)
    useEffect(() => {
        const savedTheme = (safeGetLS(THEME_KEY, null) || (JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.darkMode ? "dark" : "light")) || "light";
        const savedLang = safeGetLS(LANG_KEY, null) || JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.language || "es";

        setTheme(savedTheme);
        setLang(savedLang);
        applyTheme(savedTheme);
        i18n.changeLanguage(savedLang);

        // notifica a otros componentes (tu SettingsPanel, etc.)
        window.dispatchEvent(new CustomEvent("chat:pref:init", { detail: { theme: savedTheme, lang: savedLang } }));

        // y al host (si estamos embebidos)
        try {
            const parentOrigin = new URL(document.referrer || window.origin).origin;
            window.parent?.postMessage({ type: "prefs:update", prefs: { theme: savedTheme, language: savedLang } }, parentOrigin);
        } catch { }
    }, [i18n]);

    const closeMenu = useCallback(() => setOpen(false), []);

    // Click-outside + Escape
    useEffect(() => {
        if (!open) return;
        const onDocClick = (e) => {
            if (!menuRef.current) return;
            if (menuRef.current.contains(e.target)) return;
            if (btnRef.current && btnRef.current.contains(e.target)) return;
            setOpen(false);
        };
        const onEsc = (e) => { if (e.key === "Escape") setOpen(false); };

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
        applyTheme(next);

        // sincroniza con app:settings (no rompe el panel)
        mergeAppSettings({ darkMode: next === "dark" });

        // notifica dentro de la app
        window.dispatchEvent(new CustomEvent("chat:pref:theme", { detail: { theme: next } }));

        // notifica al host (widget)
        try {
            const parentOrigin = new URL(document.referrer || window.origin).origin;
            window.parent?.postMessage({ type: "prefs:update", prefs: { theme: next } }, parentOrigin);
        } catch { }
    };

    const changeLang = (value) => {
        setLang(value);
        safeSetLS(LANG_KEY, value);
        i18n.changeLanguage(value);

        // sincroniza con app:settings
        mergeAppSettings({ language: value });

        window.dispatchEvent(new CustomEvent("chat:pref:lang", { detail: { lang: value } }));

        try {
            const parentOrigin = new URL(document.referrer || window.origin).origin;
            window.parent?.postMessage({ type: "prefs:update", prefs: { language: value } }, parentOrigin);
        } catch { }
    };

    const handleLogout = async () => {
        try {
            if (typeof logout === "function") await logout();
            else localStorage.clear?.();
        } catch { }
        navigate("/", { replace: true });
    };

    const goZajuna = () => {
        if (!zajunaSSO) return;
        if (window.self !== window.top) window.top.location.href = zajunaSSO;
        else window.location.href = zajunaSSO;
    };

    return (
        <div className={`relative ${className}`}>
            <button
                ref={btnRef}
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50"
                aria-haspopup="menu"
                aria-expanded={open ? "true" : "false"}
                aria-label={t("config.title")}
            >
                <Settings className="w-4 h-4" />
                {t("config.title")}
            </button>

            {open && (
                <div
                    ref={menuRef}
                    role="menu"
                    className="absolute right-0 mt-2 w-80 max-w-[90vw] bg-white border shadow-lg rounded-lg p-3 z-50"
                >
                    {/* Accesibilidad */}
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">
                            {t("config.accessibility")}
                        </p>

                        <div className="flex items-center justify-between mb-2 gap-2">
                            <div className="flex items-center gap-2">
                                <Languages className="w-4 h-4 text-gray-600" />
                                <span className="text-sm">{t("config.language")}</span>
                            </div>
                            <select
                                value={lang}
                                onChange={(e) => changeLang(e.target.value)}
                                className="text-sm border rounded px-2 py-1 bg-white max-w-[50%]"
                                aria-label={t("config.language")}
                            >
                                <option value="es">Español</option>
                                <option value="en">English</option>
                            </select>
                        </div>

                        <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                                {theme === "dark" ? (
                                    <Moon className="w-4 h-4 text-gray-600" />
                                ) : (
                                    <Sun className="w-4 h-4 text-gray-600" />
                                )}
                                <span className="text-sm">{t("config.theme")}</span>
                            </div>
                            <button
                                type="button"
                                onClick={toggleTheme}
                                className="text-sm border rounded px-2 py-1 bg-white hover:bg-gray-50"
                                aria-pressed={theme === "dark"}
                            >
                                {theme === "dark" ? t("config.dark") : t("config.light")}
                            </button>
                        </div>
                    </div>

                    <hr className="my-2" />

                    {/* Panel administrativo */}
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">
                            {t("config.adminPanel")}
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <button
                                type="button"
                                onClick={() => { navigate("/admin/register"); closeMenu(); }}
                                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <UserPlus className="w-4 h-4" />
                                {t("config.registerPanel")}
                            </button>
                            <button
                                type="button"
                                onClick={() => { navigate("/admin/login"); closeMenu(); }}
                                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <Shield className="w-4 h-4" />
                                {t("config.loginPanel")}
                            </button>
                        </div>
                    </div>

                    {/* Zajuna */}
                    {zajunaSSO && (
                        <>
                            <hr className="my-2" />
                            <div className="mb-3">
                                <p className="text-xs font-semibold text-gray-500 mb-2">
                                    {t("config.zajuna")}
                                </p>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                    <button
                                        type="button"
                                        onClick={goZajuna}
                                        className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                                    >
                                        <LogIn className="w-4 h-4" />
                                        {t("config.loginZajuna")}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={goZajuna}
                                        className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                                    >
                                        <UserPlus className="w-4 h-4" />
                                        {t("config.registerZajuna")}
                                    </button>
                                </div>
                            </div>
                        </>
                    )}

                    <hr className="my-2" />

                    {/* Salir */}
                    <div className="flex justify-end">
                        <button
                            type="button"
                            onClick={handleLogout}
                            className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm text-red-600 whitespace-nowrap"
                        >
                            <LogOut className="w-4 h-4" />
                            {t("config.logout")}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
