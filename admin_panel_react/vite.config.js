// admin_panel_react/vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
    plugins: [react()],
    base: "./", // ✅ rutas relativas correctas en build (sirve bien desde Nginx)
    resolve: {
        alias: { "@": resolve(__dirname, "src") },
        dedupe: ["react", "react-dom"], // ✅ evita el doble bundle o "Invalid hook call"
    },
    optimizeDeps: {
        include: ["react", "react-dom"], // ✅ fuerza prebundle único de React
    },
    server: {
        host: true, // ✅ accesible desde red local
        port: Number(process.env.PORT) || 5173,
        strictPort: true,
        open: false,
        hmr: { overlay: false },

        allowedHosts: ["localhost", "app-dev.local"],

        headers: {
            "Access-Control-Allow-Origin": "*",
        },

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

    preview: {
        host: "localhost",
        port: 5173,
        strictPort: false,
    },

    define: {
        "process.env": {}, // ✅ evita errores al usar process.env en React
    },

    test: {
        environment: "jsdom",
        setupFiles: "./src/test/setupTests.ts", // opcional
        globals: true,
    },
});

