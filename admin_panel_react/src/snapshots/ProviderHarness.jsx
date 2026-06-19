// src/snapshots/ProviderHarness.jsx
import React from "react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ⚠️ Si tienes AuthProvider real, descomenta e importa:
// import { AuthProvider } from "@/context/AuthContext";

const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

export default function ProviderHarness({ children }) {
    const Body = (
        <QueryClientProvider client={qc}>
            <BrowserRouter>{children}</BrowserRouter>
        </QueryClientProvider>
    );

    // Si tienes AuthProvider real, envuelve Body:
    // return <AuthProvider>{Body}</AuthProvider>;
    return Body;
}
