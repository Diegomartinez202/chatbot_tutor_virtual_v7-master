import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
    Settings, LogOut, Sun, Moon, Languages,
    UserPlus, LogIn, Shield
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";

const THEME_KEY = "chat.theme";
const LANG_KEY = "chat.lang";
const APP_SETTINGS_KEY = "app:settings";

function applyTheme(theme) {
    const html = document.documentElement;
    html.classList.toggle("dark", theme === "dark");
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
    const btnRef = useRef(null);
    const menuRef = useRef(null);

    const { logout } = useAuth();
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();

    const zajunaSSO = useMemo(
        () => import.meta.env.VITE_ZAJUNA_SSO_URL || import.meta.env.VITE_ZAJUNA_LOGIN_URL || "",
        []
    );

    // cargar preferencias
    useEffect(() => {
        const savedTheme = safeGetLS(THEME_KEY, null)
            || (JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.darkMode ? "dark" : "light");
        const savedLang = safeGetLS(LANG_KEY, null)
            || JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.language
            || "es";

        setTheme(savedTheme);
        setLang(savedLang);
        applyTheme(savedTheme);
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

    const handleLogout = async () => {
        try { await logout?.(); } catch { }
        navigate("/", { replace: true });
    };

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
            >
                <Settings className="w-4 h-4" />
                {t("config.title")}
            </button>

            {open && (
                <div
                    ref={menuRef}
                    className="absolute right-0 mt-2 w-80 max-w-[90vw] bg-white border shadow-lg rounded-lg p-3 z-50"
                >
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">{t("config.accessibility")}</p>
                        {/* idioma */}
                        <div className="flex justify-between items-center mb-2">
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
                        {/* tema */}
                        <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                                {theme === "dark" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
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

                    {/* panel admin */}
                    <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 mb-2">{t("config.adminPanel")}</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            <button
                                onClick={() => { navigate("/admin/register"); setOpen(false); }}
                                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <UserPlus className="w-4 h-4" /> {t("config.registerPanel")}
                            </button>
                            <button
                                onClick={() => { navigate("/admin/login"); setOpen(false); }}
                                className="inline-flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm"
                            >
                                <Shield className="w-4 h-4" /> {t("config.loginPanel")}
                            </button>
                        </div>
                    </div>

                    {/* zajuna */}
                    {zajunaSSO && (
                        <>
                            <hr className="my-2" />
                            <p className="text-xs font-semibold text-gray-500 mb-2">{t("config.zajuna")}</p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                <button onClick={goZajuna} className="flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm">
                                    <LogIn className="w-4 h-4" /> {t("config.loginZajuna")}
                                </button>
                                <button onClick={goZajuna} className="flex items-center gap-2 px-3 py-2 border rounded bg-white hover:bg-gray-50 text-sm">
                                    <UserPlus className="w-4 h-4" /> {t("config.registerZajuna")}
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
                            <LogOut className="w-4 h-4" /> {t("config.logout")}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
