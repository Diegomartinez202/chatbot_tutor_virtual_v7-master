import React, { useEffect } from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import ChatPage from "@/pages/ChatPage";

/**
 * Simula un flujo multi-turno sin backend.
 * Sobrescribe fetch para /api/chat/history y /api/chat/send|message.
 * NO toca fixtures.js.
 */
export default function ChatScenarioHarness() {
    useEffect(() => {
        const originalFetch = window.fetch;

        // Escenario demo (ajústalo si quieres otro)
        const history = [
            { role: "user", text: "Hola, ¿qué puedo estudiar hoy?" },
            { role: "assistant", text: "¡Hola! Te sugiero empezar por Álgebra básica. ¿Te muestro un temario?" },
            { role: "user", text: "Sí, por favor." },
            { role: "assistant", text: "Temario: 1) Operaciones con enteros 2) Fracciones 3) Ecuaciones. ¿Cuál te interesa?" },
        ];

        function jsonResponse(body, init = {}) {
            return new Response(JSON.stringify(body), {
                status: 200,
                headers: { "Content-Type": "application/json" },
                ...init,
            });
        }

        window.fetch = async (input, init) => {
            const url = typeof input === "string" ? input : input.url;

            // Historial inicial del chat
            if (url.includes("/api/chat/history")) {
                return jsonResponse({ messages: history, has_more: false });
            }

            // Envío de mensaje → responder con texto "didáctico"
            if (url.includes("/api/chat/send") || url.includes("/api/chat/message")) {
                let userMsg = "";
                try {
                    const payload = typeof init?.body === "string" ? JSON.parse(init.body) : init?.body;
                    userMsg = payload?.text || payload?.message || "";
                } catch { }

                // Respuesta simple en base a las palabras clave
                let reply =
                    "Puedo guiarte paso a paso. Por ejemplo: empieza con sumas y restas de enteros. ¿Quieres un ejercicio?";
                if (/fracci/i.test(userMsg)) reply = "Para fracciones: simplifica numerador y denominador. ¿Vemos un ejemplo?";
                if (/ecuaci/i.test(userMsg)) reply = "Ecuaciones lineales: pasa términos a un lado y despeja la incógnita.";

                // Simula latencia
                await new Promise((r) => setTimeout(r, 500));
                return jsonResponse({ reply, tokens: 64, finish_reason: "stop" });
            }

            // Salud
            if (url.includes("/api/chat/health") || url.includes("/api/health")) {
                return jsonResponse({ ok: true });
            }

            // Default
            return originalFetch(input, init);
        };

        return () => {
            window.fetch = originalFetch;
        };
    }, []);

    return (
        <ProviderHarness>
            <div className="p-4">
                <h1 className="text-xl font-semibold mb-4">Chat — Escenario multi-turno (Harness)</h1>
                {/* Usa embed si tu ChatPage lo soporta; si no, quita forceEmbed */}
                <ChatPage forceEmbed />
            </div>
        </ProviderHarness>
    );
}