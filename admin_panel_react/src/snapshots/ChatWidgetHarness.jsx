import React, { useEffect, useRef, useState } from "react";
import ProviderHarness from "@/snapshots/ProviderHarness";

/**
 * Carga el widget real embebido inyectando /chat-widget.js.
 * Requiere que tengas en /public: chat-widget.js y chat-embed.html
 */
export default function ChatWidgetHarness() {
    const [loaded, setLoaded] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        // Limpia cualquier script previo
        const prev = document.querySelector('script[data-harness-widget="1"]');
        if (prev) prev.remove();

        const base = window.location.origin.replace(/\/$/, "");
        const script = document.createElement("script");
        script.src = `${base}/chat-widget.js`;
        script.async = true;
        script.dataset.harnessWidget = "1";
        script.setAttribute("data-chat-url", `${base}/chat-embed.html?src=${encodeURIComponent("/chat?embed=1")}`);
        script.setAttribute("data-avatar", `${base}/bot-avatar.png`);
        script.setAttribute("data-badge", "auto");
        script.setAttribute("data-allowed-origins", base);
        script.onload = () => setLoaded(true);

        document.body.appendChild(script);
        return () => {
            script.remove();
            // Remueve iframe/render del widget si lo dejo en el DOM
            const frames = document.querySelectorAll('iframe[title="Chat"], iframe[title="Chatbot"]');
            frames.forEach((n) => n.remove());
        };
    }, []);

    return (
        <ProviderHarness>
            <div className="p-6 space-y-3" ref={containerRef}>
                <h1 className="text-xl font-semibold">Chat — Widget embebido (Harness)</h1>
                <p className="text-sm text-gray-600">
                    {loaded ? "Widget cargado. Usa el launcher inferior derecho." : "Cargando widget…"}
                </p>
            </div>
        </ProviderHarness>
    );
}