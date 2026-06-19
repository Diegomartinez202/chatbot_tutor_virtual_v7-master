// src/hooks/useChatSettingsListener.js
import { useEffect } from "react";

export default function useChatSettingsListener({
    onTheme,
    onContrast,
    onLang,
} = {}) {
    useEffect(() => {
        const handler = (ev) => {
            try {
                const { type, theme, contrast, lang } = ev.data || {};
                if (type !== "chat:settings") return;

                // Aplica a la app React si quieres
                if (typeof onTheme === "function") onTheme(theme);
                if (typeof onContrast === "function") onContrast(contrast);
                if (typeof onLang === "function") onLang(lang);

                // También opcional: modificar <html> dentro del iframe/app
                const html = document.documentElement;
                if (theme === "dark") html.classList.add("dark");
                else html.classList.remove("dark");

                if (contrast) document.body.classList.add("high-contrast");
                else document.body.classList.remove("high-contrast");
            } catch { }
        };

        window.addEventListener("message", handler);
        return () => window.removeEventListener("message", handler);
    }, [onTheme, onContrast, onLang]);
}