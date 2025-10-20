// src/snapshots/useHarnessMocks.js
import { useEffect } from "react";
import { statsMock, logsMock } from "@/snapshots/fixtures";

/**
 * Activa mocks en runtime SIN tocar tu API real.
 * Se enciende si:
 *  - force === true (por defecto en harness)
 *  - o si hay ?mock=1 en la URL
 *  - o si import.meta.env.VITE_USE_STATS_MOCK === "true"
 */
export default function useHarnessMocks(force = true) {
    useEffect(() => {
        const urlHasMock = typeof window !== "undefined" && new URLSearchParams(window.location.search).has("mock");
        const envMock = (import.meta?.env?.VITE_USE_STATS_MOCK ?? "").toString() === "true";
        const active = force || urlHasMock || envMock;
        if (!active) return;

        const originalFetch = window.fetch.bind(window);

        function json(data, status = 200, headers = {}) {
            return new Response(JSON.stringify(data), {
                status,
                headers: { "Content-Type": "application/json", ...headers },
            });
        }

        function text(body, status = 200, headers = {}) {
            return new Response(body, { status, headers });
        }

        window.fetch = async (input, init = {}) => {
            try {
                const req = typeof input === "string" ? input : input.url;
                const method = (init.method || "GET").toUpperCase();

                // ---- STATS ----
                if (/\/api\/stats(\b|\/)/.test(req)) {
                    return json(statsMock);
                }

                // ---- LOGS ----
                if (/\/api\/logs(\b|\/)/.test(req)) {
                    return json(logsMock);
                }

                // ---- AUTH / USERS ----
                if (/\/api\/users\/me(\b|\/)/.test(req)) {
                    return json({
                        id: "u_123",
                        email: "admin@demo.com",
                        name: "Admin Demo",
                        roles: ["admin", "soporte"],
                    });
                }

                if (/\/api\/auth\/refresh(\b|\/)/.test(req)) {
                    return json({
                        access_token: "mocked.token.value",
                        token_type: "Bearer",
                        expires_in: 3600,
                    });
                }

                // ---- EXPORTACIONES ----
                if (/\/api\/exportaciones\/.+\/download(\b|\/)?$/.test(req)) {
                    return text("id,evento,fecha\n1,descarga_mock,2025-08-14", 200, { "Content-Type": "text/csv" });
                }
                if (/\/api\/exportaciones(\b|\/)/.test(req)) {
                    return json({
                        total: 3,
                        items: [
                            { id: "exp_1", tipo: "logs_csv", estado: "completado", creado_en: "2025-08-14T09:00:00Z", url: "/api/exportaciones/exp_1/download" },
                            { id: "exp_2", tipo: "stats_json", estado: "en_proceso", creado_en: "2025-08-14T10:00:00Z" },
                            { id: "exp_3", tipo: "intents_xlsx", estado: "fallido", creado_en: "2025-08-14T11:00:00Z", error: "Timeout" },
                        ],
                    });
                }

                // ---- HEALTH / STATUS ----
                if (/\/admin\/rasa\/status(\b|\/)|\/api\/health(\b|\/)|\/api\/chat\/health(\b|\/)/.test(req)) {
                    return json({ ok: true, status: "healthy" });
                }

                // ---- INTENTS / CONFUSIONS ----
                if (/\/api\/intents(\b|\/)/.test(req)) {
                    return json({
                        total: 4,
                        items: [
                            { name: "saludo", ejemplos: ["hola", "buenas"], updated_at: "2025-08-10T12:00:00Z" },
                            { name: "despedida", ejemplos: ["chao", "hasta luego"], updated_at: "2025-08-11T12:00:00Z" },
                            { name: "consulta_envio", ejemplos: ["cuando llega", "estado del pedido"], updated_at: "2025-08-12T12:00:00Z" },
                            { name: "problema_pago", ejemplos: ["no puedo pagar", "error con tarjeta"], updated_at: "2025-08-13T12:00:00Z" },
                        ],
                    });
                }

                if (/\/api\/confusions\/top(\b|\/)/.test(req)) {
                    return json({
                        total: 3,
                        items: [
                            { intent: "nlu_fallback", count: 12, example: "no entiendo esto" },
                            { intent: "faq_envio", count: 4, example: "cuando llega?" },
                            { intent: "faq_pagos", count: 3, example: "no puedo pagar" },
                        ],
                    });
                }

                // ---- CHAT ----
                if (/\/api\/chat\/history(\b|\/)/.test(req)) {
                    return json({
                        conversation_id: "conv_1",
                        items: [
                            { id: "m1", role: "user", text: "Hola", ts: Date.now() - 60_000 },
                            { id: "m2", role: "assistant", text: "¡Hola! ¿En qué te ayudo?", ts: Date.now() - 59_000 },
                        ],
                    });
                }

                if (/\/api\/chat\/(send|message)(\b|\/)/.test(req) && method === "POST") {
                    let userText = "mensaje";
                    try {
                        if (init.body) {
                            const ct = (init.headers && (init.headers["Content-Type"] || init.headers["content-type"])) || "";
                            if (typeof init.body === "string") {
                                if (ct.includes("application/json")) {
                                    const body = JSON.parse(init.body);
                                    userText = body?.text || body?.message || userText;
                                } else {
                                    userText = init.body || userText;
                                }
                            }
                        }
                    } catch { }
                    return json({
                        reply: {
                            id: `m_${Math.random().toString(36).slice(2, 8)}`,
                            role: "assistant",
                            text: `Respuesta mock para: “${userText}”`,
                            ts: Date.now(),
                        },
                    });
                }

                // Por defecto → red real
                return originalFetch(input, init);
            } catch {
                return originalFetch(input, init);
            }
        };

        return () => {
            window.fetch = originalFetch;
        };
    }, [force]);
}