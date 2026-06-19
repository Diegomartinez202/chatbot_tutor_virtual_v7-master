// src/components/chat/rasa/restClient.js
export async function sendToRasaREST(senderId, text, token) {
    const url = (import.meta.env.VITE_CHAT_REST_URL || "/api/chat").replace(/\/$/, "") + "/rasa/rest/webhook";

    const metadata = {
        auth: {
            hasToken: !!token,
            // opcional: token en crudo si tu backend lo valida (no necesario si ya validas en proxy)
            // token
        },
    };

    const body = {
        sender: senderId || "web",
        message: text,
        metadata,
    };

    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
        credentials: "include",
    });

    if (!res.ok) {
        const tx = await res.text().catch(() => "");
        throw new Error(tx || `HTTP ${res.status}`);
    }
    return await res.json();
}
