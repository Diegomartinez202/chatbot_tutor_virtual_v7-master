import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en/translation.json";
import es from "./locales/es/translation.json";

const savedLang = localStorage.getItem("app:settings")
    ? JSON.parse(localStorage.getItem("app:settings")).language
    : "es";

i18n.use(initReactI18next).init({
    resources: {
        en: { translation: en },
        es: { translation: es },
    },
    lng: savedLang || "es",
    fallbackLng: "es",
    interpolation: { escapeValue: false },
});

export default i18n;