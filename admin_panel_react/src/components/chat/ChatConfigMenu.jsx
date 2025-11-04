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
    const { t, i18n } = useTranslation("config");
    const navigate = useNavigate();

    const zajunaSSO = useMemo(
        () => import.meta.env.VITE_ZAJUNA_SSO_URL || import.meta.env.VITE_ZAJUNA_LOGIN_URL || "",
        []
    );

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

    const goZajuna = () => {
        if (!zajunaSSO) return;
        window.top.location.href = zajunaSSO;
    };
}
