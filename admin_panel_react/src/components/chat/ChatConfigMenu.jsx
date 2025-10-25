// src/components/chat/ChatConfigMenu.jsx
import { useEffect, useMemo, useState } from "react";
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

function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === "dark") html.classList.add("dark");
    else html.classList.remove("dark");
}

export default function ChatConfigMenu({ className = "" }) {
    const [open, setOpen] = useState(false);
    const [theme, setTheme] = useState("light");
    const [lang, setLang] = useState("es");

    const navigate = useNavigate();
    const { logout } = useAuth();
    const { t, i18n } = useTranslation(); // ✅ usamos claves "config.*"

    const zajunaSSO = useMemo(
        () =>
            import.meta.env.VITE_ZAJUNA_SSO_URL ||
            import.meta.env.VITE_ZAJUNA_LOGIN_URL ||
            "",
        []
    );

    // Cargar preferencias guardadas y aplicarlas
    useEffect(() => {
        try {
            const savedTheme = localStorage.getItem(THEME_KEY) || "light";
            const savedLang = localStorage.getItem(LANG_KEY) || "es";
            setTheme(savedTheme);
            setLang(savedLang);
            applyTheme(savedTheme);
            i18n.changeLanguage(savedLang);
            window.dispatchEvent(
                new CustomEvent("chat:pref:init", {
                    detail: { theme: savedTheme, lang: savedLang },
                })
            );
        } catch { }
    }, [i18n]);

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        try { localStorage.setItem(THEME_KEY, next); } catch { }
        applyTheme(next);
        window.dispatchEvent(
            new CustomEvent("chat:pref:theme", { detail: { theme: next } })
        );
    };

    const changeLang = (value) => {
        setLang(value);
        try { localStorage.setItem(LANG_KEY, value); } catch { }
        i18n.changeLanguage(value);
        window.dispatchEvent(
            new CustomEvent("chat:pref:lang", { detail: { lang: value } })
        );
    };

    const handleLogout = async () => {
        try {
            if (typeof logout === "function") await logout();
            else localStorage.clear?.();
        } catch { }
        navigate("/", { replace: true });
    };

    const goZajuna = () => {
        if (zajunaSSO) window.location.href = zajunaSSO;
    };

    return (
        <div className={`relative ${className}`}>
            {/* ✅ Este es el botón que USAS: se queda y traduce bien */}
            <button
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
                    role="menu"
                    className="absolute right-0 mt-2 w-80 bg-white border shadow-lg rounded-lg p-3 z-50"
                >
                    {/* Accesibilidad */}
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">
                            {t("config.accessibility")}
                        </p>

                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <Languages className="w-4 h-4 text-gray-600" />
                                <span className="text-sm">{t("config.language")}</span>
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

                        <div className="flex items-center justify-between">
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
                        <div className="flex flex-col gap-2">
                            <button
                                type="button"
                                onClick={() => navigate("/admin/register")}
                                className="w-full inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <UserPlus className="w-4 h-4" />
                                {t("config.registerPanel")}
                            </button>
                            <button
                                type="button"
                                onClick={() => navigate("/admin/login")}
                                className="w-full inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
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
                                <div className="flex flex-col gap-2">
                                    <button
                                        type="button"
                                        onClick={goZajuna}
                                        className="w-full inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                                    >
                                        <LogIn className="w-4 h-4" />
                                        {t("config.loginZajuna")}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={goZajuna}
                                        className="w-full inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
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