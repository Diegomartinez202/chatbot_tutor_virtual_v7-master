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
        host: true,                                // o '0.0.0.0'
        port: Number(process.env.PORT) || 5173,
        strictPort: true,                          // ← antes estaba en false
        open: false,
        hmr: { overlay: false },

        // ✅ Permite el host que usas con Nginx
        allowedHosts: ["app-dev.local", "localhost"],

        // ✅ Cabecera útil si embebes o usas proxy/iframe
        headers: {
            "Access-Control-Allow-Origin": "*",
        },

        // Tu proxy original (se mantiene igual)
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

    // 🧪 ✅ Vitest (se conserva)
    test: {
        environment: "jsdom",
        setupFiles: "./src/test/setupTests.ts", // opcional
        globals: true,
    },
});
