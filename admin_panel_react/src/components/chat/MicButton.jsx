// src/components/chat/MicButton.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
    Mic,
    Square,
    Upload,
    Repeat2,
    X,
    Loader2,
    Play,
    Pause,
} from "lucide-react";

/**
 * MicButton
 * - Graba audio con MediaRecorder (WebM/Opus u Ogg/Opus).
 * - Previsualiza y sube por POST a `${CHAT_REST}/audio`.
 * - Llama a onPushUser(transcript) y onPushBot(rasaMessages).
 *
 * Props:
 * - onPushUser: (text) => void
 * - onPushBot: (messagesArray) => void
 * - userId?: string      (opcional; si no, lo resuelve el backend con session_id/anon)
 * - persona?: string     (opcional)
 * - lang?: string        (default "es" | "auto")
 * - sessionId?: string   (opcional)
 * - token?: string       (opcional; si proteges /audio con Bearer)
 */
export default function MicButton({
    onPushUser,
    onPushBot,
    userId = null,
    persona = null,
    lang = "es",
    sessionId = null,
    token = null,
    disabled = false,
}) {
    // Usa el mismo base que el resto del chat
    const CHAT_REST = import.meta.env.VITE_CHAT_REST_URL || "/api/chat";
    const AUDIO_URL = useMemo(
        () => `${String(CHAT_REST).replace(/\/$/, "")}/audio`,
        [CHAT_REST]
    );

    const [supported, setSupported] = useState(true);
    const [recording, setRecording] = useState(false);
    const [blob, setBlob] = useState(null);
    const [mime, setMime] = useState("audio/webm");
    const [previewUrl, setPreviewUrl] = useState("");
    const [uploading, setUploading] = useState(false);
    const [err, setErr] = useState("");
    const [elapsed, setElapsed] = useState(0);
    const [playing, setPlaying] = useState(false);

    const chunksRef = useRef([]);
    const recRef = useRef(null);
    const timerRef = useRef(null);
    const audioElRef = useRef(null);

    // Soporte básico
    useEffect(() => {
        if (!window.MediaRecorder) {
            setSupported(false);
            return;
        }
        const prefers = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/ogg;codecs=opus",
            "audio/ogg",
        ];
        let chosen = "";
        for (const t of prefers) {
            try {
                if (window.MediaRecorder.isTypeSupported(t)) {
                    chosen = t;
                    break;
                }
            } catch { }
        }
        setMime(chosen || "audio/webm");
    }, []);

    useEffect(() => {
        if (blob) {
            const url = URL.createObjectURL(blob);
            setPreviewUrl(url);
            return () => URL.revokeObjectURL(url);
        } else {
            setPreviewUrl("");
        }
    }, [blob]);

    // timer de grabación
    const startTimer = () => {
        setElapsed(0);
        clearInterval(timerRef.current);
        timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    };
    const stopTimer = () => {
        clearInterval(timerRef.current);
        timerRef.current = null;
    };

    const startRecording = async () => {
        if (disabled || uploading) return;
        setErr("");
        setBlob(null);
        setPlaying(false);

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const rec = new MediaRecorder(stream, { mimeType: mime });
            recRef.current = rec;
            chunksRef.current = [];

            rec.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
            };
            rec.onstop = () => {
                try {
                    stream.getTracks().forEach((t) => t.stop());
                } catch { }
                stopTimer();
                const b = new Blob(chunksRef.current, { type: mime || "audio/webm" });
                setBlob(b);
                setRecording(false);
            };

            rec.start(100); // recolecta chunks ~100ms
            startTimer();
            setRecording(true);
        } catch (e) {
            console.error(e);
            setErr(
                "No se pudo acceder al micrófono. Revisa permisos del navegador/dispositivo."
            );
            setRecording(false);
        }
    };

    const stopRecording = () => {
        try {
            recRef.current?.stop();
        } catch { }
    };

    const discard = () => {
        setBlob(null);
        setErr("");
        setPlaying(false);
        try {
            if (audioElRef.current) {
                audioElRef.current.pause();
                audioElRef.current.currentTime = 0;
            }
        } catch { }
    };

    const togglePlay = async () => {
        const el = audioElRef.current;
        if (!el) return;
        if (playing) {
            el.pause();
            setPlaying(false);
        } else {
            try {
                await el.play();
                setPlaying(true);
            } catch (e) {
                console.error(e);
            }
        }
    };

    const upload = async () => {
        if (!blob || uploading) return;
        setUploading(true);
        setErr("");

        try {
            // 15MB aprox: coherente con el backend
            if (blob.size > 15 * 1024 * 1024) {
                setErr("El audio es demasiado grande (máx. 15 MB).");
                setUploading(false);
                return;
            }

            const file = new File([blob], "voice.webm", { type: mime || "audio/webm" });
            const fd = new FormData();
            fd.append("file", file);
            if (userId) fd.append("user_id", userId);
            if (persona) fd.append("persona", persona);
            if (lang) fd.append("lang", lang);
            if (sessionId) fd.append("session_id", sessionId);

            const headers = token ? { Authorization: `Bearer ${token}` } : undefined;

            const rsp = await fetch(AUDIO_URL, {
                method: "POST",
                body: fd,
                headers,
            });

            if (!rsp.ok) {
                const txt = await rsp.text().catch(() => "");
                throw new Error(txt || `Error ${rsp.status}`);
            }

            const data = await rsp.json();
            const transcript = (data && data.transcript) || "";
            const botMsgs = (data && data.bot && data.bot.messages) || [];

            if (transcript) onPushUser?.(transcript);
            if (Array.isArray(botMsgs)) onPushBot?.(botMsgs);

            // reset
            setBlob(null);
            setUploading(false);
            setPlaying(false);
        } catch (e) {
            console.error(e);
            setErr(e?.message || "Error al subir el audio");
            setUploading(false);
        }
    };

    if (!supported) {
        return (
            <button
                type="button"
                title="Micrófono no soportado"
                className="inline-flex items-center justify-center rounded-md bg-gray-200 text-gray-500 px-3 py-2 cursor-not-allowed"
                disabled
                data-testid="mic-unsupported"
            >
                <Mic className="w-4 h-4" />
            </button>
        );
    }

    // Estados:
    // - Idle: botón mic → startRecording
    // - Recording: botón stop + timer
    // - Preview: <audio> + Enviar / Regrabar / Cancelar
    // - Uploading: spinner
    return (
        <div className="inline-flex items-center gap-2">
            {/* Estado grabación */}
            {recording ? (
                <button
                    type="button"
                    onClick={stopRecording}
                    className="inline-flex items-center justify-center rounded-md bg-red-600 text-white px-3 py-2 hover:bg-red-700"
                    aria-label="Detener grabación"
                    data-testid="mic-stop"
                >
                    <Square className="w-4 h-4" />
                    <span className="ml-2 text-xs" data-testid="mic-timer">
                        {formatSeconds(elapsed)}
                    </span>
                </button>
            ) : blob ? (
                // Preview
                <div className="flex items-center gap-2">
                    <audio
                        ref={audioElRef}
                        src={previewUrl}
                        onPause={() => setPlaying(false)}
                        onEnded={() => setPlaying(false)}
                        className="hidden"
                    />
                    <button
                        type="button"
                        onClick={togglePlay}
                        className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50"
                        aria-label={playing ? "Pausar" : "Reproducir"}
                        data-testid={playing ? "mic-pause" : "mic-play"}
                    >
                        {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button
                        type="button"
                        onClick={upload}
                        disabled={uploading || disabled}
                        className="inline-flex items-center justify-center rounded-md bg-indigo-600 text-white px-3 py-2 hover:bg-indigo-700 disabled:opacity-50"
                        aria-label="Enviar audio"
                        data-testid="mic-upload"
                    >
                        {uploading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <>
                                <Upload className="w-4 h-4" />
                                <span className="ml-2 text-xs">Enviar</span>
                            </>
                        )}
                    </button>
                    <button
                        type="button"
                        onClick={startRecording}
                        disabled={uploading || disabled}
                        className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50"
                        aria-label="Regrabar"
                        title="Regrabar"
                        data-testid="mic-rerecord"
                    >
                        <Repeat2 className="w-4 h-4" />
                    </button>
                    <button
                        type="button"
                        onClick={discard}
                        disabled={uploading}
                        className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50"
                        aria-label="Cancelar"
                        title="Cancelar"
                        data-testid="mic-cancel"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            ) : (
                // Idle
                <button
                    type="button"
                    onClick={startRecording}
                    disabled={disabled}
                    className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50 disabled:opacity-50"
                    aria-label="Grabar audio"
                    title="Grabar audio"
                    data-testid="mic-button"   /* compat con nuevos tests */
                >
                    {/* compat con specs antiguos que buscaban "chat-mic" */}
                    <span className="sr-only" data-testid="chat-mic" />
                    <Mic className="w-4 h-4" />
                </button>
            )}

            {/* Error inline */}
            {err ? (
                <span className="text-xs text-red-600" data-testid="mic-error">
                    {err}
                </span>
            ) : null}
        </div>
    );
}

function formatSeconds(s) {
    const m = Math.floor(s / 60)
        .toString()
        .padStart(2, "0");
    const ss = (s % 60).toString().padStart(2, "0");
    return `${m}:${ss}`;
}