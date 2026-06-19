import React, { useEffect } from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";
import ChatPage from "@/pages/ChatPage";

/**
 * Modo kiosko (fullscreen, sin chrome del site):
 * - Fuerza embed (no exige login).
 * - Mockea /api/chat/*, /api/users/me, /api/auth/refresh, /api/health.
 * - Usa embedHeight="100vh" (sin hacks).
 * - Saludo inicial configurable: window.CHATBOT_GREETING o localStorage.CHATBOT_GREETING.
 */
export default function ChatKioskHarness() {
    useEffect(() => {
        const originalFetch = window.fetch;

        const greeting =
            (typeof window !== "undefined" && window.CHATBOT_GREETING) ||
            (typeof localStorage !== "undefined" && localStorage.getItem("CHATBOT_GREETING")) ||
            "¡Hola! Soy tu tutor virtual. ¿En qué puedo ayudarte hoy?";

        const initialHistory = [
            { role: "assistant", text: greeting },
            { role: "user", text: "Quiero practicar fracciones" },
            { role: "assistant", text: "Perfecto. ¿Empezamos con una explicación corta y un ejemplo?" },
        ];

        function json(body, init = {}) {
            return new Response(JSON.stringify(body), {
                status: 200,
                headers: { "Content-Type": "application/json" },
                ...init,
            });
        }

        window.fetch = async (input, init) => {
            const url = typeof input === "string" ? input : input.url;

            // Auth opcional (por si algo lo invoca)
            if (url.includes("/api/users/me")) {
                return json({ id: "kiosk", email: "demo@kiosk.local", roles: ["user"] });
            }
            if (url.includes("/api/auth/refresh")) {
                return json({ access_token: "mock-token" });
            }

            // Salud / diagnóstico
            if (url.includes("/api/chat/health") || url.includes("/api/health")) {
                return json({ ok: true, service: "chat" });
            }

            // Historial del chat
            if (url.includes("/api/chat/history")) {
                return json({ messages: initialHistory, has_more: false });
            }

            // Envío de mensajes
            if (url.includes("/api/chat/send") || url.includes("/api/chat/message")) {
                let userMsg = "";
                try {
                    const payload = typeof init?.body === "string" ? JSON.parse(init.body) : init?.body;
                    userMsg = payload?.text || payload?.message || "";
                } catch { }

                let reply =
                    "Puedo ayudarte con Álgebra, Fracciones y Ecuaciones. Dime un tema y te muestro ejercicios.";
                if (/fracci/i.test(userMsg)) reply = "Para fracciones: simplifica numerador y denominador. ¿Vemos un ejemplo?";
                if (/ecuaci/i.test(userMsg))
                    reply = "Ecuaciones: pasa términos al otro lado y despeja la incógnita. ¿Quieres practicar una?";

                await new Promise((r) => setTimeout(r, 400)); // latencia de demo
                return json({ reply, tokens: 64, finish_reason: "stop" });
            }

            return originalFetch(input, init);
        };

        return () => {
            window.fetch = originalFetch;
        };
    }, []);

    return (
        <ProviderHarness>
            <div className="w-screen h-screen bg-gray-50 overflow-hidden">
                <ChatPage
                    forceEmbed
                    embedHeight="100vh"     // ← usa el prop nuevo
                    title="Asistente — Modo Kiosko"
                    connectFn={async () => {
                        await new Promise((r) => setTimeout(r, 250));
                        return true;
                    }}
                />
            </div>
        </ProviderHarness>
    );
}