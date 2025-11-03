// src/services/chatClient.js
// Stub minimal para Rasa REST (y ganchos para socket si luego lo usas)

const DEFAULT_BASE = import.meta.env.VITE_RASA_BASE_URL || "http://localhost:5005";

// POST /webhooks/rest/webhook { sender, message }
export async function sendTextMessage({ baseUrl = DEFAULT_BASE, sender, text }) {
    const url = `${baseUrl.replace(/\/$/, "")}/webhooks/rest/webhook`;
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender, message: text }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    // Rasa devuelve array [{text}, {image}, ...]
    return await res.json();
}

// Conexión "fake" para estados del loader (puedes reemplazar por socket real)
export async function connectChat({ baseUrl = DEFAULT_BASE }) {
    // Simula latencia de conexión
    await new Promise((r) => setTimeout(r, 300));
    // Si quieres validar health:
    // const health = await fetch(`${baseUrl.replace(/\/$/, "")}/status`);
    return { ok: true };
}