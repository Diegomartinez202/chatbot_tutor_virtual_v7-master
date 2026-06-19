// src/snapshots/fixtures.js
export const statsMock = {
    summary: { total_messages: 345, bot_success: 290, not_understood: 24, avg_response_ms: 420, accuracy: 0.89 },
    series: {
        by_day: [
            { date: "2025-08-10", messages: 40, success: 35, fallback: 3 },
            { date: "2025-08-11", messages: 52, success: 46, fallback: 4 },
            { date: "2025-08-12", messages: 63, success: 51, fallback: 7 },
            { date: "2025-08-13", messages: 70, success: 60, fallback: 6 },
            { date: "2025-08-14", messages: 80, success: 65, fallback: 9 },
        ],
        latency_ms_p50: [
            { date: "2025-08-10", value: 350 },
            { date: "2025-08-11", value: 400 },
            { date: "2025-08-12", value: 430 },
            { date: "2025-08-13", value: 410 },
            { date: "2025-08-14", value: 395 },
        ],
        latency_ms_p95: [
            { date: "2025-08-10", value: 800 },
            { date: "2025-08-11", value: 900 },
            { date: "2025-08-12", value: 950 },
            { date: "2025-08-13", value: 860 },
            { date: "2025-08-14", value: 910 },
        ],
    },
    top_confusions: [
        { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
        { intent: "faq_envio", count: 4, example: "cuando llega?" },
        { intent: "faq_pagos", count: 3, example: "no puedo pagar" },
    ],
};

export const logsMock = {
    total: 20,
    items: Array.from({ length: 20 }).map((_, i) => ({
        _id: `log_${i + 1}`,
        request_id: `req_${1000 + i}`,
        sender_id: i % 3 === 0 ? "anonimo" : `user_${i}`,
        user_message: i % 5 === 0 ? "No puedo ingresar" : "Hola, necesito ayuda",
        bot_response: ["Claro, te ayudo con eso."],
        intent: i % 4 === 0 ? "problema_no_ingreso" : "saludo",
        timestamp: new Date(Date.now() - i * 3600_000).toISOString(),
        ip: "127.0.0.1",
        user_agent: "PlaywrightBot/1.0",
        origen: i % 3 === 0 ? "widget" : "autenticado",
        metadata: { mocked: true },
    })),
};
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
