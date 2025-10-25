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
        host: true, // escucha en 0.0.0.0 (útil en Docker)
        port: Number(process.env.PORT) || 5173,
        strictPort: false,
        open: false, // evita xdg-open
        hmr: {
            overlay: false, // sin overlay rojo
        },
        proxy: {
            "/static": {
                // Si usas Docker con red interna, cambia a "http://backend:8000"
                target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
                changeOrigin: true,
            },
            // Si quieres también proxyear la API en dev, descomenta:
            "/api": {
            target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
            changeOrigin: true,
            },
        },
    },

    preview: {
        host: true,
        port: 5173,
        strictPort: false,
        open: false,
    },

    // Evita "process is not defined" si algún código lee process.env
    define: {
        "process.env": {},
    },
});