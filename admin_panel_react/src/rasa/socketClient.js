// admin_panel_react/src/rasa/socketClient.js
import { io } from "socket.io-client";
import { buildRasaMetadata } from "./meta.js";

let socket = null;

export function getSocket() {
    if (!socket) {
        // Conexión directa a Rasa:
        socket = io("http://localhost:5005", {
            path: "/socket.io/",
            transports: ["websocket"],
            withCredentials: true,
        });
    }
    return socket;
}

export function sendToRasaSocket(text) {
    const s = getSocket();
    s.emit("user_uttered", {
        message: String(text || ""),
        metadata: buildRasaMetadata(),
    });
}
