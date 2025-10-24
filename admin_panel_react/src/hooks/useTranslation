import { useState } from "react";
import es from "@/locales/es/translation.json";
import en from "@/locales/en/translation.json";

const locales = { es, en };

export function useTranslation() {
  const [lang] = useState("es"); // podrías hacerlo dinámico

  const t = (path) => {
    const keys = path.split(".");
    let value = locales[lang];
    for (const key of keys) {
      value = value?.[key];
      if (value === undefined) return path;
    }
    return value;
  };

  return t;
}