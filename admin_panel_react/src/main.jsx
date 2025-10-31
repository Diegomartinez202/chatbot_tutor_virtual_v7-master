// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";

// 🛠 Estilos base
import "@/styles/index.css";
import "@/styles/animations.css";

// ✅ Cargar i18n ANTES de montar React y ANTES de importar App
import "@/i18n";

import { AuthProvider } from "@/context/AuthContext";
import { QueryClientProvider } from "@tanstack/react-query";
import queryClient from "@/lib/react-query";
import { Toaster } from "react-hot-toast";
import { ThemeProvider } from "@/context/ThemeContext";

// ⚠️ Tu archivo es src/app.jsx (minúsculas)
import App from "@/app.jsx";

import { BrowserRouter } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { setAccessTokenGetter } from "@/state/tokenProvider";

// 🧩 Bridge de autenticación (recibe auth:token desde el host/burbuja)
import { initAuthBridge } from "@/embed/authBridge.js";

// ─────────────────────────────────────────────────────────────
// Safeguard: si #root no existe, créalo (evita pantalla en blanco)
// ─────────────────────────────────────────────────────────────
let rootEl = document.getElementById("root");
if (!rootEl) {
    rootEl = document.createElement("div");
    rootEl.id = "root";
    document.body.appendChild(rootEl);
}

// ─────────────────────────────────────────────────────────────
// Conectar getter de token (Zustand) para el cliente REST de Rasa
// ─────────────────────────────────────────────────────────────
setAccessTokenGetter(() => {
    // snapshot inmediato del estado, sin hooks
    return useAuthStore.getState().accessToken || null;
});

// ─────────────────────────────────────────────────────────────
// Inicializar el bridge de auth del iframe UNA sola vez
// Esto permite que, cuando la burbuja envía `auth:token`,
// el iframe lo reciba y tus llamadas a Rasa salgan con
// metadata.auth.hasToken = true.
// ─────────────────────────────────────────────────────────────
(function initBridgeOnce() {
    // 1) Intenta tomar origin permitido desde ENV (coma-separado). Usa el primero.
    const env = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "")
        .split(",")
        .map(s => String(s || "").trim().replace(/\/+$/, ""))
        .filter(Boolean);

    // 2) Si no hay ENV, intenta con el origin del referrer (host que incrusta el iframe)
    let fallbackOrigin = "*";
    try {
        const ref = document.referrer ? new URL(document.referrer).origin : "";
        if (ref) fallbackOrigin = ref;
    } catch {
        // ignora
    }

    const originToAllow = env[0] || fallbackOrigin || "*";
    initAuthBridge(originToAllow);
})();

// ─────────────────────────────────────────────────────────────
// Montaje React
// ─────────────────────────────────────────────────────────────
ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
        <AuthProvider>
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <ThemeProvider>
                        <App />
                    </ThemeProvider>
                </BrowserRouter>
                <Toaster position="top-right" />
            </QueryClientProvider>
        </AuthProvider>
    </React.StrictMode>
);
