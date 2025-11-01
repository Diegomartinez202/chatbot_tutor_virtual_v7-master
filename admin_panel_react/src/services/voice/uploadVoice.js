// src/services/voice/uploadVoice.js
import axiosClient from "@/services/axiosClient";

export async function uploadVoiceBlob(blob, { sender, lang = "es", stt = "auto" } = {}) {
    const fd = new FormData();
    fd.append("file", blob, "voice.webm");
    fd.append("sender", sender);
    fd.append("lang", lang);
    fd.append("stt", stt);

    const { data } = await axiosClient.post("/api/voice/transcribe", fd, {
        headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
}
