// src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "@/App";
import "@/styles/index.css";
import './styles/animations.css';
import { AuthProvider } from "@/context/AuthContext";
import { QueryClientProvider } from "@tanstack/react-query";
import queryClient from "@/lib/react-query";
import { Toaster } from "react-hot-toast";

import { RouterProvider } from "react-router-dom";
import { router } from "@/router";

// Salvaguarda: si #root no existe, créalo (evita pantalla en blanco)
let rootEl = document.getElementById("root");
if (!rootEl) {
    rootEl = document.createElement("div");
    rootEl.id = "root";
    document.body.appendChild(rootEl);
}

ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                {/* Data Router con flags v7 activos */}
                <RouterProvider router={router} />
                <Toaster position="top-right" />
            </AuthProvider>
        </QueryClientProvider>
    </React.StrictMode>
);