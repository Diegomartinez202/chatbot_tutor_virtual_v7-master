// src/i18n.js
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// ES
import es_common from "./locales/es/common.json";
import es_chat from "./locales/es/chat.json";
import es_config from "./locales/es/config.json";

// EN
import en_common from "./locales/en/common.json";
import en_chat from "./locales/en/chat.json";
import en_config from "./locales/en/config.json";

// Detectar idioma guardado o navegador (JS puro)
function detectLang() {
    try {
        const stored = localStorage.getItem("app:settings");
        if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed?.language === "en" || parsed?.language === "es") {
                return parsed.language;
            }
        }
    } catch { }
    const nav = (typeof navigator !== "undefined" && navigator.language)
        ? navigator.language.toLowerCase()
        : "es";
    return nav.startsWith("en") ? "en" : "es";
}

const initialLng = detectLang();

i18n
    .use(initReactI18next)
    .init({
        resources: {
            es: { common: es_common, chat: es_chat, config: es_config },
            en: { common: en_common, chat: en_chat, config: en_config },
        },
        lng: initialLng,
        fallbackLng: "es",
        ns: ["common", "chat", "config"],
        defaultNS: "common",
        interpolation: { escapeValue: false },
    });

// Persistir cuando cambie el idioma
i18n.on("languageChanged", (lng) => {
    try {
        const current = JSON.parse(localStorage.getItem("app:settings") || "{}");
        current.language = lng === "en" ? "en" : "es";
        localStorage.setItem("app:settings", JSON.stringify(current));
    } catch { }
});

export default i18n;