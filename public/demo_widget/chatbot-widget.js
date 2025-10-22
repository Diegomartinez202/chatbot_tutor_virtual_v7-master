document.addEventListener("DOMContentLoaded", () => {
    // === Configuración ===
    const chatbot = document.createElement("div");
    chatbot.id = "chatbot-widget";
    chatbot.innerHTML = `
    <div id="chatbot-header">🤖 Tutor Virtual Zajuna</div>
    <div id="chatbot-messages"></div>
    <div id="chatbot-input">
      <input type="text" placeholder="Escribe un mensaje..." id="chat-input" />
      <button id="send-btn">Enviar</button>
    </div>
  `;
    document.body.appendChild(chatbot);

    // === Detectar tema ===
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.body.dataset.theme = prefersDark ? "dark" : "light";

    // === Elementos ===
    const messages = document.getElementById("chatbot-messages");
    const input = document.getElementById("chat-input");
    const send = document.getElementById("send-btn");

    // === Función para mostrar mensajes ===
    const sendMessage = (msg, sender) => {
        const message = document.createElement("div");
        message.className = `message ${sender}`;
        message.textContent = msg;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    };

    // === URL del backend ===
    const BACKEND_URL = "http://127.0.0.1:8000/chat";
    const DEMO_URL = "http://127.0.0.1:8000/chat/demo";

    async function sendToBackend(message) {
        const payload = { sender: "anonimo", message };

        try {
            const response = await fetch(BACKEND_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error("Rasa no disponible");

            const data = await response.json();
            if (Array.isArray(data)) {
                data.forEach((msg) => msg.text && sendMessage(msg.text, "bot"));
            } else {
                sendMessage("🤖 Respuesta inesperada del backend.", "bot");
            }
        } catch {
            // Fallback demo si falla la conexión real
            const demoRes = await fetch(DEMO_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const demoData = await demoRes.json();
            demoData.forEach((msg) => msg.text && sendMessage(msg.text, "bot"));
        }
    }

    // === Envío de mensaje ===
    send.addEventListener("click", () => {
        const text = input.value.trim();
        if (!text) return;
        sendMessage(text, "user");
        input.value = "";
        sendToBackend(text);
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") send.click();
    });

    // === Mensaje inicial ===
    sendMessage("¡Hola! Soy tu tutor virtual Zajuna 💬", "bot");

    // === Drag & Drop ===
    const header = document.getElementById("chatbot-header");
    let isDragging = false, offsetX, offsetY;

    header.addEventListener("mousedown", (e) => {
        isDragging = true;
        const rect = chatbot.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        chatbot.style.transition = "none";
    });

    document.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        chatbot.style.left = `${e.clientX - offsetX}px`;
        chatbot.style.top = `${e.clientY - offsetY}px`;
        chatbot.style.right = "auto";
        chatbot.style.bottom = "auto";
    });

    document.addEventListener("mouseup", () => {
        isDragging = false;
        chatbot.style.transition = "0.2s ease";
    });

    // === Botón de tema ===
    const toggle = document.getElementById("theme-toggle");
    toggle.addEventListener("click", () => {
        document.body.dataset.theme = document.body.dataset.theme === "dark" ? "light" : "dark";
    });
});