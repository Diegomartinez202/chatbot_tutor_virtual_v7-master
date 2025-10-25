import React, { useEffect, useState } from "react";
import { Moon, Sun, Contrast } from "lucide-react";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/IconTooltip";

export default function ThemeToggle() {
  const [theme, setTheme] = useState("light");
  const [highContrast, setHighContrast] = useState(false);

  // Leer desde localStorage al iniciar
  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("app:settings") || "{}");
    if (saved.darkMode) setTheme("dark");
    if (saved.highContrast) setHighContrast(true);
    document.documentElement.classList.toggle("dark", saved.darkMode);
    document.documentElement.classList.toggle("high-contrast", saved.highContrast);
  }, []);

  // Guardar cambios
  const updateStorage = (updates) => {
    const saved = JSON.parse(localStorage.getItem("app:settings") || "{}");
    const merged = { ...saved, ...updates };
    localStorage.setItem("app:settings", JSON.stringify(merged));
  };

  const toggleDark = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
    updateStorage({ darkMode: newTheme === "dark" });
  };

  const toggleContrast = () => {
    const newHC = !highContrast;
    setHighContrast(newHC);
    document.documentElement.classList.toggle("high-contrast", newHC);
    updateStorage({ highContrast: newHC });
  };

  return (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        {/* Modo oscuro */}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={toggleDark}
              className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              aria-label={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            {theme === "dark" ? "Modo claro" : "Modo oscuro"}
          </TooltipContent>
        </Tooltip>

        {/* Alto contraste */}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={toggleContrast}
              className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              aria-label="Alternar alto contraste"
            >
              <Contrast size={18} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            {highContrast ? "Desactivar alto contraste" : "Activar alto contraste"}
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}