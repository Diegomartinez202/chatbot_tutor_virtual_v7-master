// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "@/styles/index.css";
import "@/styles/animations.css";

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

// ✅ Importar i18n antes de montar React
import "@/i18n";

// Salvaguarda: si #root no existe, créalo (evita pantalla en blanco)
let rootEl = document.getElementById("root");
if (!rootEl) {
    rootEl = document.createElement("div");
    rootEl.id = "root";
    document.body.appendChild(rootEl);
}

// Inyecta el getter del token desde Zustand (no rompe nada si no hay token)
setAccessTokenGetter(() => {
    // ✅ usar el snapshot inmediato del estado (sin hooks)
    return useAuthStore.getState().accessToken || null;
});

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
