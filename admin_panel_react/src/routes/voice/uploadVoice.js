// src/services/voice/uploadVoice.js  (NUEVO)
export async function uploadVoiceBlob(blob, { sender, lang = "es", stt = "auto" } = {}) {
    const fd = new FormData();
    fd.append("file", blob, `voice-${Date.now()}.webm`);
    if (sender) fd.append("sender", sender);
    fd.append("lang", lang);
    fd.append("stt", stt);

    const res = await fetch("/api/voice/transcribe", {
        method: "POST",
        body: fd,
        credentials: "include",
    });
    if (!res.ok) throw new Error(`uploadVoice: ${res.status} ${await res.text()}`);
    return res.json(); // { id, transcript, duration_ms, mime }
}
