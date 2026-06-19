// admin_panel_react/src/services/chat/connectRasaRest.js

export const DEFAULT_CHAT_URL =
    (import.meta?.env?.VITE_CHAT_REST_URL && String(import.meta.env.VITE_CHAT_REST_URL).trim())
    || "/chat"; // detrás de Nginx

export async function connectRasaRest() {
    const url = `${DEFAULT_CHAT_URL.replace(/\/$/, "")}/health`;
    const res = await fetch(url, { method: "GET", credentials: "include" });
    if (!res.ok) throw new Error(`Healthcheck failed: ${res.status}`);
    return true;
}

export async function sendRasaMessage({ text, sender, metadata = {}, baseUrl, token } = {}) {
    if (!text || !String(text).trim()) throw new Error("Mensaje vacío");
    const host = String(baseUrl || DEFAULT_CHAT_URL).replace(/\/$/, "");
    const url = `${host}/rasa/rest/webhook`;

    const authToken =
        token || (typeof localStorage !== "undefined" ? localStorage.getItem("zajuna_token") : null);

    const headers = { "Content-Type": "application/json" };
    if (authToken) headers.Authorization = `Bearer ${authToken}`;

    const body = {
        sender: sender || getOrCreateSenderId(),
        message: text,
        metadata: { ...metadata, auth: { hasToken: !!authToken } },
    };

    const res = await fetch(url, { method: "POST", headers, credentials: "include", body: JSON.stringify(body) });
    if (!res.ok) throw new Error(`REST ${res.status}: ${(await res.text().catch(() => "")) || "error al enviar mensaje"}`);
    const data = await res.json().catch(() => []);
    return Array.isArray(data) ? data : [];
}

// —— Helpers —— //
const SENDER_KEY = "chat_sender_id";
function getOrCreateSenderId() {
    try {
        const existing = localStorage.getItem(SENDER_KEY);
        if (existing) return existing;
        const id = `web-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
        localStorage.setItem(SENDER_KEY, id);
        return id;
    } catch {
        return `web-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
    }
}
