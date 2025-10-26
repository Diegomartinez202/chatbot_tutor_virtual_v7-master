// admin_panel_react/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
    plugins: [react()],
    base: "./",
    resolve: {
        alias: { "@": resolve(__dirname, "src") },
    },
    server: {
        host: true,
        port: Number(process.env.PORT) || 5173,
        strictPort: false,
        open: false,
        hmr: { overlay: false },
        proxy: {
            "/static": { target: "http://backend-dev:8000", changeOrigin: true },
            "/api": { target: "http://backend-dev:8000", changeOrigin: true },
            "/rasa": {
                target: "http://rasa:5005",
                changeOrigin: true,
                rewrite: (p) => p.replace(/^\/rasa/, ""),
            },
            "/ws": {
                target: "ws://rasa:5005",
                changeOrigin: true,
                ws: true,
                rewrite: (p) => p.replace(/^\/ws/, ""),
            },
        },
    },
    preview: { host: "localhost", port: 5173, strictPort: false },
    define: { "process.env": {} },

    // 🧪 ✅ Añadido: configuración mínima de Vitest
    test: {
        environment: "jsdom",
        setupFiles: "./src/test/setupTests.ts", // opcional (lo creamos abajo)
        globals: true,
    },
});
