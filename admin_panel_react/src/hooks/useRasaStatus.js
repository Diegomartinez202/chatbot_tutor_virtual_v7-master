// admin_panel_react/src/hooks/useRasaStatus.js
import { useState, useEffect, useCallback } from "react";

// Base de la API (Nginx te sirve frontend y backend en el mismo host/puerto)
const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

// Health del canal REST que definimos en backend/routes/chat.py
const RASA_STATUS_URL =
    import.meta.env.VITE_RASA_STATUS_URL ||
    `${API_BASE}/chat/rasa/rest/webhook/health`;

export default function useRasaStatus() {
    const [status, setStatus] = useState("connecting");

    const checkStatus = useCallback(async () => {
        setStatus("connecting");

        try {
            const response = await fetch(RASA_STATUS_URL, { method: "GET" });

            console.log("Rasa status response:", response);

            if (!response.ok) {
                throw new Error(`Bad HTTP status: ${response.status}`);
            }

            // Intentamos leer el JSON para validar que el backend diga "ok"
            let data = null;
            try {
                data = await response.json();
                console.log("Rasa status JSON:", data);
            } catch (e) {
                console.warn("No se pudo parsear JSON de health:", e);
            }

            // Si hay JSON y dice status: "ok", damos por bueno
            if (data && data.status && data.status !== "ok") {
                throw new Error(`Rasa status != ok (${data.status})`);
            }

            setStatus("ready");
        } catch (err) {
            console.error("Error conectando a Rasa:", err);
            setStatus("error");
        }
    }, []);

    useEffect(() => {
        checkStatus();
    }, [checkStatus]);

    return { status, checkStatus };
}

