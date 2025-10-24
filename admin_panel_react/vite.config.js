// admin_panel_react/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
    plugins: [react()],

    // útil para despliegues en subdirectorios (GitHub Pages, etc.)
    base: "./",

    // Alias @ → src
    resolve: {
        alias: {
            "@": resolve(__dirname, "src"),
        },
    },

    server: {
        host: "localhost",
        port: Number(process.env.PORT) || 5173,
        strictPort: false, // Si el puerto está ocupado, usa otro
        open: true,
        hmr: {
            overlay: false, // 🚫 Desactiva el overlay rojo de errores en el navegador
        },
    },

    preview: {
        host: "localhost",
        port: 5173,
        strictPort: false,
    },

    // Evita "process is not defined" si algún código lee process.env
    define: {
        "process.env": {},
    },
});