import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en/translation.json";
import es from "./locales/es/translation.json";

// 🔹 Leer idioma guardado en localStorage
let savedLang = "es";
try {
    const stored = localStorage.getItem("app:settings");
    if (stored) {
        const parsed = JSON.parse(stored);
        savedLang = parsed.language || "es";
    }
} catch {
    savedLang = "es";
}

// 🔹 Inicializar i18next
i18n.use(initReactI18next).init({
    resources: {
        en: { translation: en },
        es: { translation: es },
    },
    lng: savedLang, // idioma inicial
    fallbackLng: "es",
    interpolation: { escapeValue: false },
    detection: {
        order: ["localStorage", "navigator"],
        caches: ["localStorage"],
    },
});

// 🔹 Reaccionar dinámicamente a cambios
i18n.on("languageChanged", (lng) => {
    try {
        const settings = JSON.parse(localStorage.getItem("app:settings")) || {};
        settings.language = lng;
        localStorage.setItem("app:settings", JSON.stringify(settings));
    } catch { }
});

export default i18n;