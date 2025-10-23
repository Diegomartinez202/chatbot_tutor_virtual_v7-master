import React from "react";
import ReactDOM from "react-dom/client";

import "@/styles/index.css";
import "@/styles/animations.css";

import { AuthProvider } from "@/context/AuthContext";
import { QueryClientProvider } from "@tanstack/react-query";
import queryClient from "@/lib/react-query";
import { Toaster } from "react-hot-toast";

// ⚠️ Tu archivo es src/app.jsx (minúsculas)
import App from "@/app.jsx";

import { BrowserRouter } from "react-router-dom";

// Salvaguarda: si #root no existe, créalo (evita pantalla en blanco)
let rootEl = document.getElementById("root");
if (!rootEl) {
    rootEl = document.createElement("div");
    rootEl.id = "root";
    document.body.appendChild(rootEl);
}

ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
        <AuthProvider>
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <App />
                </BrowserRouter>
                <Toaster position="top-right" />
            </QueryClientProvider>
        </AuthProvider>
    </React.StrictMode>
);