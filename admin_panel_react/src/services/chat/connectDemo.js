// src/services/chat/connectDemo.js
export async function connectDemo() {
    // Simula una conexión "ok"
    await new Promise((r) => setTimeout(r, 600));
    return true;
}