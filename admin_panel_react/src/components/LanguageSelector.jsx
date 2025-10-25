import React, { useEffect, useState } from "react";
import { Languages } from "lucide-react";
import i18n from "@/i18n";
import {
    Tooltip,
    TooltipTrigger,
    TooltipContent,
    TooltipProvider,
} from "@/components/ui/IconTooltip";

export default function LanguageSelector() {
    const [lang, setLang] = useState(i18n.language || "es");

    const handleChange = (e) => {
        const newLang = e.target.value;
        setLang(newLang);
        i18n.changeLanguage(newLang);

        // Persistir idioma en localStorage
        const settings = JSON.parse(localStorage.getItem("app:settings") || "{}");
        settings.language = newLang;
        localStorage.setItem("app:settings", JSON.stringify(settings));
    };

    // Asegura que el idioma se aplique al recargar
    useEffect(() => {
        i18n.changeLanguage(lang);
    }, [lang]);

    return (
        <TooltipProvider>
            <div className="flex items-center gap-2">
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Languages size={18} className="text-gray-700 dark:text-gray-200" />
                    </TooltipTrigger>
                    <TooltipContent side="bottom">Seleccionar idioma</TooltipContent>
                </Tooltip>

                <select
                    value={lang}
                    onChange={handleChange}
                    className="border rounded px-2 py-1 text-sm bg-white dark:bg-zinc-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
                    aria-label="Seleccionar idioma"
                >
                    <option value="es">🇪🇸 Español</option>
                    <option value="en">🇬🇧 English</option>
                </select>
            </div>
        </TooltipProvider>
    );
}
