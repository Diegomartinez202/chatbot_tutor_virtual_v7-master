// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";

// 🛠 Estilos base
import "@/styles/index.css";
import "@/styles/animations.css";

import "@/i18n";

import { AuthProvider } from "@/context/AuthContext";
import { QueryClientProvider } from "@tanstack/react-query";
import queryClient from "@/lib/react-query";
import { Toaster } from "react-hot-toast";
import { ThemeProvider } from "@/context/ThemeContext";

import App from "@/app.jsx";

import { BrowserRouter } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { setAccessTokenGetter } from "@/state/tokenProvider";

import { initAuthBridge } from "@/embed/authBridge.js";
import { STORAGE_KEYS } from "@/lib/constants";
import { setAuthToken } from "@/services/axiosClient";

const APP_CONTEXT =
    (typeof window !== "undefined" && (window as any).APP_CONTEXT) || "panel";

const IS_EMBEDDED =
    typeof window !== "undefined" && window.self !== window.top;

// Asegura el root
let rootEl = document.getElementById("root");
if (!rootEl) {
    rootEl = document.createElement("div");
    rootEl.id = "root";
    document.body.appendChild(rootEl);
}

// 👉 expone el getter de token a axiosClient (tu store sigue intacto)
setAccessTokenGetter(() => {
    return useAuthStore.getState().accessToken || null;
});

// 👉 puente de autenticación (solo si embebido/híbrido)
(function initBridgeOnce() {
    if (!(IS_EMBEDDED || APP_CONTEXT === "hybrid")) return;

    const env = (import.meta.env.VITE_ALLOWED_HOST_ORIGINS || "")
        .split(",")
        .map((s: string) => String(s || "").trim().replace(/\/+$/, ""))
        .filter(Boolean);

    let fallbackOrigin = "*";
    try {
        const ref = document.referrer ? new URL(document.referrer).origin : "";
        if (ref) fallbackOrigin = ref;
    } catch {
        // no-op
    }

    const originToAllow = env[0] || fallbackOrigin || "*";
    initAuthBridge(originToAllow);
})();

// ✅ Bootstrap del token: el primer /auth/me ya lleva Authorization
(function bootstrapAuth() {
    try {
        const t = localStorage.getItem(STORAGE_KEYS.accessToken);
        if (t) setAuthToken(t); // deja el header Authorization listo
    } catch {
        // no-op
    }
})();

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
