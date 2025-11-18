import { useState, useEffect, useCallback } from "react";

const RASA_STATUS_URL =
    import.meta.env.VITE_RASA_STATUS_URL ||
    `${(import.meta.env.VITE_API_BASE || "http://localhost:8000/api").replace(/\/$/, "")}/chat/health`;

export default function useRasaStatus() {
    const [status, setStatus] = useState("connecting");

    const checkStatus = useCallback(async () => {
        setStatus("connecting");

        try {
            const response = await fetch(RASA_STATUS_URL, { method: "GET" });

            if (!response.ok) throw new Error("Bad status");

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
