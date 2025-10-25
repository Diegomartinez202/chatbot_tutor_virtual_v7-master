// admin_panel_react/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
    plugins: [react()],

    // útil si alguna vez sirves en subcarpetas
    base: "./",

    resolve: {
        alias: {
            "@": resolve(__dirname, "src"),
        },
    },

    server: {
        host: true,                     // escucha en 0.0.0.0 dentro del contenedor
        port: Number(process.env.PORT) || 5173,
        strictPort: false,
        open: false,                    // evita xdg-open en Linux/containers
        hmr: { overlay: false },

        // 🔁 PROXY: desde Vite → a servicios del compose
        // - En DEV con tus servicios actuales, desde el contenedor de Vite
        //   el backend se llama http://backend-dev:8000 (¡no localhost!)
        proxy: {
            // estáticos del backend (FastAPI mount /static) => evita el MIME text/html
            "/static": {
                target: "http://backend-dev:8000",
                changeOrigin: true,
            },

            // si quieres pegarle a la API directamente durante el dev (opcional):
            "/api": {
                target: "http://backend-dev:8000",
                changeOrigin: true,
            },

            // si quieres pegarle directo a Rasa desde Vite (opcional):
            // OJO: ya tienes Nginx dev para esto; si usas 8080, no lo necesitas.
            "/rasa": {
                target: "http://rasa:5005",
                changeOrigin: true,
                rewrite: (p) => p.replace(/^\/rasa/, ""), // /rasa/... -> /
            },
            "/ws": {
                target: "ws://rasa:5005",
                changeOrigin: true,
                ws: true,
                rewrite: (p) => p.replace(/^\/ws/, ""), // /ws -> /
            },
        },
    },

    preview: {
        host: "localhost",
        port: 5173,
        strictPort: false,
    },

    define: {
        "process.env": {},
    },
});