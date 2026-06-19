// src/components/chat/ChatConfigMenu.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
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
    Contrast,
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
function safeGetLS(k, f) {
    try {
        return localStorage.getItem(k) ?? f;
    } catch {
        return f;
    }
}
function safeSetLS(k, v) {
    try {
        localStorage.setItem(k, v);
    } catch { }
}
function mergeAppSettings(patch) {
    try {
        const raw = localStorage.getItem(APP_SETTINGS_KEY);
        const cur = raw ? JSON.parse(raw) : {};
        localStorage.setItem(APP_SETTINGS_KEY, JSON.stringify({ ...cur, ...patch }));
    } catch { }
}

/** Pequeños helpers visuales para que todo se vea uniforme  */
function SectionTitle({ children }) {
    return (
        <div className="px-1 pt-3 pb-1 text-[11px] font-semibold tracking-wide text-indigo-100 uppercase opacity-90">
            {children}
        </div>
    );
}

function MenuButton({
    icon: Icon,
    label,
    helper,
    onClick,
    danger = false,
    align = "between",
}) {
    const justify =
        align === "start"
            ? "justify-start"
            : align === "center"
                ? "justify-center"
                : "justify-between";

    return (
        <button
            type="button"
            onClick={onClick}
            className={`
        w-full flex ${justify} items-center gap-2
        px-3 py-1.5               /* 👈 más bajos */
        text-[13px]               /* 👈 texto un poco más pequeño */
        rounded-xl
        border shadow-sm transition-all
        mb-3                      /* 👈 más espacio entre botones */
        ${danger
                    ? "bg-rose-500 text-white border-rose-300 hover:bg-rose-400"
                    : "bg-indigo-500 text-white border-indigo-300 hover:bg-indigo-400"
                }
      `}
        >
            <span className="inline-flex items-center gap-2">
                {Icon && <Icon className="w-4 h-4 shrink-0" />}
                <span className="font-medium">{label}</span>
            </span>

            {helper && (
                <span className="text-[11px] text-indigo-50/90 font-medium">
                    {helper}
                </span>
            )}
        </button>
    );
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
        () =>
            (import.meta.env.VITE_ZAJUNA_SSO_URL ||
                import.meta.env.VITE_ZAJUNA_LOGIN_URL ||
                "").trim(),
        []
    );

    /* ------- Estado inicial desde localStorage ------- */
    useEffect(() => {
        const savedTheme =
            safeGetLS(THEME_KEY, null) ||
            (JSON.parse(safeGetLS(APP_SETTINGS_KEY, "{}"))?.darkMode
                ? "dark"
                : "light");

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
        document.documentElement.setAttribute(
            "lang",
            savedLang === "en" ? "en" : "es"
        );
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
        window.parent?.postMessage(
            { type: "prefs:update", prefs: { theme: next } },
            "*"
        );
    };

    const changeLang = (val) => {
        const lang = val === "en" ? "en" : "es";
        setLang(lang);
        safeSetLS(LANG_KEY, lang);
        i18n.changeLanguage(lang);
        mergeAppSettings({ language: lang });
        document.documentElement.setAttribute("lang", lang);
        window.parent?.postMessage(
            { type: "prefs:update", prefs: { language: lang } },
            "*"
        );
    };

    const toggleContrast = () => {
        const next = !highContrast;
        setHighContrast(next);
        safeSetLS(CONTRAST_KEY, next ? "1" : "0");
        applyHighContrast(next);
        mergeAppSettings({ highContrast: next });
        window.parent?.postMessage(
            { type: "prefs:update", prefs: { highContrast: next } },
            "*"
        );
    };

    const handleLogout = async () => {
        try {
            await logout?.();
        } catch { }
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
    const handleExitChat = () => {
        setOpen(false);
        navigate("/", { replace: true });
    };
    const langLabel = lang === "en" ? "English" : "Español";
    const themeLabel = theme === "dark" ? "Oscuro" : "Claro";
    const contrastLabel = highContrast
        ? "Alto contraste: ON"
        : "Alto contraste: OFF";

    return (
        <div className={`relative ${className}`}>
            {/* Botón que vive en el navbar, junto a "Salir" */}
            <button
                type="button"
                ref={btnRef}
                onClick={() => setOpen((v) => !v)}
                className="inline-flex items-center px-4 py-1.5 rounded-full border border-white/50 bg-white/10 text-xs sm:text-sm font-medium text-white hover:bg-white/20 backdrop-blur shadow-sm"
                aria-haspopup="menu"
                aria-expanded={open}
            >
                Configuración
            </button>

            {open && (
                <div
                    ref={menuRef}
                    role="menu"
                    className="
      absolute mt-2 left-0
      w-72 max-w-[min(18rem,calc(100vw-1.5rem))]
      rounded-2xl
      border-2 border-indigo-300
      bg-indigo-700 text-indigo-50
      shadow-2xl
      p-3
      z-50
      space-y-3
    "
                >
                    {/* CABECERA */}
                    <div className="flex items-center justify-between pb-2 border-b border-indigo-300/60">
                        <span className="text-[12px] font-semibold tracking-wide uppercase">
                            Ajustes del chat
                        </span>
                        <button
                            type="button"
                            onClick={() => setOpen(false)}
                            className="px-2 py-1 text-[11px] rounded-full bg-indigo-500 hover:bg-indigo-400 text-white transition"
                        >
                            Cerrar
                        </button>
                    </div>
                    {/* === ACCESIBILIDAD (tema, contraste, idioma) === */}
                    <SectionTitle>Accesibilidad</SectionTitle>

                    <MenuButton
                        icon={theme === "dark" ? Moon : Sun}
                        label="Tema"
                        helper={themeLabel}
                        onClick={toggleTheme}
                    />

                    <MenuButton
                        icon={Contrast}
                        label="Alto contraste"
                        helper={contrastLabel}
                        onClick={toggleContrast}
                    />

                    <div className="px-1 pt-2 pb-1 flex items-center justify-between gap-2">
                        <span className="text-[13px] text-indigo-50 font-semibold">
                            Idioma
                        </span>

                        <div className="flex gap-2">
                            <button
                                type="button"
                                aria-label="Cambiar a Español"
                                onClick={() => changeLang("es")}
                                className={`
        px-3 py-1.5 text-[11px] rounded-full border
        transition-all font-semibold
        ${lang === "es"
                                        ? "bg-white text-indigo-600 border-white shadow-sm"
                                        : "bg-indigo-500 text-indigo-50 border-indigo-300 hover:bg-indigo-400"
                                    }
      `}
                            >
                                ES
                            </button>

                            <button
                                type="button"
                                aria-label="Switch to English"
                                onClick={() => changeLang("en")}
                                className={`
        px-3 py-1.5 text-[11px] rounded-full border
        transition-all font-semibold
        ${lang === "en"
                                        ? "bg-white text-indigo-600 border-white shadow-sm"
                                        : "bg-indigo-500 text-indigo-50 border-indigo-300 hover:bg-indigo-400"
                                    }
      `}
                            >
                                EN
                            </button>
                        </div>
                    </div>


                    <div className="px-3 pb-2 text-[11px] text-slate-400">
                         {langLabel}
                    </div>

                    <div className="h-px bg-indigo-300/50 mx-1 my-2 rounded-full" />

                    {/* === CHATBOT: autenticarse con Zajuna para el bot === */}
                    <SectionTitle>Chatbot</SectionTitle>

                    <MenuButton
                        label="Autenticarse con Zajuna"
                        onClick={goZajuna}
                        align="center"
                    />

                    <div className="h-px bg-indigo-300/50 mx-1 my-2 rounded-full" />

                    {/* === PANEL ADMINISTRATIVO (app) === */}
                    <SectionTitle>Panel administrativo</SectionTitle>

                    <MenuButton
                        label="Iniciar sesión"
                        onClick={goLoginApp}
                        align="center"
                    />

                    <MenuButton
                        label="Registrarse"
                        onClick={goRegisterApp}
                        align="center"
                    />
                    <MenuButton
                        label="Registrarse / ingresar con Zajuna"
                        onClick={goZajuna}
                        align="center"
                    />
                    {isAuthenticated && (
                        <>
                            <div className="h-px bg-indigo-300/50 mx-1 my-2 rounded-full" />
                            <MenuButton
                                label="Cerrar sesión"
                                danger
                                onClick={handleLogout}
                            />
                        </>
                    )}
                    <div className="h-px bg-indigo-300/50 mx-1 my-2 rounded-full" />
                            <SectionTitle>Chat</SectionTitle>

                    <MenuButton
                        label="Salir del chat"
                        onClick={handleExitChat}
                        align="center"
                    />
                </div>
            )}
        </div >
    );
}
