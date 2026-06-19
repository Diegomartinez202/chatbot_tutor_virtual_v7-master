// admin_panel_react/src/components/chat/MicButton.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Mic, Square, Upload, Repeat2, X, Loader2, Play, Pause } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import { uploadVoiceBlob } from "@/services/voice/uploadVoice";

function isSecureContextLike() {
    const isLocalhost = /^localhost$|^127\.0\.0\.1$|^::1$/.test(location.hostname);
    return window.isSecureContext || isLocalhost;
}
function pickBestMime() {
    const ua = navigator.userAgent.toLowerCase();
    const prefers = ua.includes("firefox")
        ? ["audio/ogg;codecs=opus", "audio/ogg", "audio/webm;codecs=opus", "audio/webm"]
        : ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/ogg"];
    for (const t of prefers) {
        try { if (window.MediaRecorder?.isTypeSupported?.(t)) return t; } catch { }
    }
    return "audio/webm";
}
function formatSeconds(s) {
    const m = Math.floor(s / 60).toString().padStart(2, "0");
    const ss = (s % 60).toString().padStart(2, "0");
    return `${m}:${ss}`;
}

/**
 * MicButton (nuevo, sin legacy)
 * Props:
 *  - onVoice?: (text) => void
 *  - lang?: "es" | "en" | ...
 *  - stt?:  "auto" | "none"  (si no tienes STT real, usa "none")
 *  - disabled?: boolean
 */
export default function MicButton({ onVoice, lang = "es", stt = "auto", disabled = false }) {
    const t = useTranslation();

    const [supported, setSupported] = useState(true);
    const [recording, setRecording] = useState(false);
    const [blob, setBlob] = useState(null);
    const [mime, setMime] = useState("audio/webm");
    const [previewUrl, setPreviewUrl] = useState("");
    const [uploading, setUploading] = useState(false);
    const [err, setErr] = useState("");
    const [elapsed, setElapsed] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [permState, setPermState] = useState("prompt");

    const chunksRef = useRef([]);
    const recRef = useRef(null);
    const timerRef = useRef(null);
    const audioElRef = useRef(null);

    // Soporte + contexto seguro + MIME óptimo
    useEffect(() => {
        if (!isSecureContextLike()) {
            setSupported(false);
            setErr(t("mic.secure_required") || "El micrófono requiere HTTPS o localhost.");
            return;
        }
        if (!window.MediaRecorder || !navigator.mediaDevices) {
            setSupported(false);
            setErr(t("mic.not_supported") || "Grabación no soportada en este navegador.");
            return;
        }
        setMime(pickBestMime());
    }, [t]);

    // Estado de permisos (si el navegador lo soporta)
    useEffect(() => {
        let mounted = true;
        if (navigator.permissions?.query) {
            navigator.permissions
                .query({ name: "microphone" })
                .then((p) => {
                    if (!mounted) return;
                    setPermState(p.state);
                    p.onchange = () => mounted && setPermState(p.state);
                })
                .catch(() => setPermState("unknown"));
        } else setPermState("unknown");
        return () => { mounted = false; };
    }, []);

    useEffect(() => {
        if (blob) {
            const url = URL.createObjectURL(blob);
            setPreviewUrl(url);
            return () => URL.revokeObjectURL(url);
        } else setPreviewUrl("");
    }, [blob]);

    const startTimer = () => {
        setElapsed(0);
        clearInterval(timerRef.current);
        timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    };
    const stopTimer = () => { clearInterval(timerRef.current); timerRef.current = null; };

    const startRecording = async () => {
        if (disabled || uploading) return;
        setErr(""); setBlob(null); setPlaying(false);

        if (!navigator.mediaDevices?.getUserMedia) {
            setSupported(false);
            setErr(t("mic.not_supported") || "Grabación no soportada en este navegador.");
            return;
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const rec = new MediaRecorder(stream, { mimeType: mime });
            recRef.current = rec;
            chunksRef.current = [];

            rec.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunksRef.current.push(e.data); };
            rec.onstop = () => {
                try { stream.getTracks().forEach((t) => t.stop()); } catch { }
                stopTimer();
                const b = new Blob(chunksRef.current, { type: mime || "audio/webm" });
                setBlob(b);
                setRecording(false);
            };

            rec.start(100);
            startTimer();
            setRecording(true);
        } catch (e) {
            const denied = (e && /denied|notallowed|permission/i.test(String(e.name || e.message))) || permState === "denied";
            setErr(denied
                ? (t("mic.permission_denied") || "Permiso de micrófono denegado en el navegador.")
                : (t("mic.no_access") || "No se pudo acceder al micrófono.")
            );
            setRecording(false);
        }
    };
    const stopRecording = () => { try { recRef.current?.stop(); } catch { } };

    const discard = () => {
        setBlob(null); setErr(""); setPlaying(false);
        try { if (audioElRef.current) { audioElRef.current.pause(); audioElRef.current.currentTime = 0; } } catch { }
    };
    const togglePlay = async () => {
        const el = audioElRef.current; if (!el) return;
        if (playing) { el.pause(); setPlaying(false); }
        else { try { await el.play(); setPlaying(true); } catch (e) { console.error(e); } }
    };

    const upload = async () => {
        if (!blob || uploading) return;
        setUploading(true); setErr("");
        try {
            if (blob.size > 15 * 1024 * 1024) { setErr(t("mic.too_large") || "El audio es demasiado grande."); return; }
            const sender = localStorage.getItem("chat_sender_id") || "web";
            const r = await uploadVoiceBlob(blob, { sender, lang, stt }); // → POST /api/voice/transcribe
            const txt = (r && r.transcript) ? String(r.transcript).trim() : "[audio enviado]";
            onVoice && onVoice(txt);
            setBlob(null); setPlaying(false);
        } catch (e) {
            const msg = e?.response?.data?.message || e?.response?.data?.detail || e?.message || (t("mic.upload_error") || "No se pudo subir el audio.");
            setErr(msg);
        } finally { setUploading(false); }
    };

    if (!supported) {
        return (
            <button type="button" title={err || t("mic.not_supported")} className="inline-flex items-center justify-center rounded-md bg-gray-200 text-gray-500 px-3 py-2 cursor-not-allowed" disabled>
                <Mic className="w-4 h-4" />
            </button>
        );
    }

    return (
        <div className="inline-flex items-center gap-2">
            {recording ? (
                <button type="button" onClick={stopRecording} className="inline-flex items-center justify-center rounded-md bg-red-600 text-white px-3 py-2 hover:bg-red-700" aria-label={t("mic.stop_recording")}>
                    <Square className="w-4 h-4" />
                    <span className="ml-2 text-xs">{formatSeconds(elapsed)}</span>
                </button>
            ) : blob ? (
                <div className="flex items-center gap-2">
                    <audio ref={audioElRef} src={previewUrl} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} className="hidden" />
                    <button type="button" onClick={togglePlay} className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50" aria-label={playing ? t("mic.pause") : t("mic.play")}>
                        {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button type="button" onClick={upload} disabled={uploading || disabled} className="inline-flex items-center justify-center rounded-md bg-indigo-600 text-white px-3 py-2 hover:bg-indigo-700 disabled:opacity-50" aria-label={t("mic.send_audio")}>
                        {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><Upload className="w-4 h-4" /><span className="ml-2 text-xs">{t("mic.send")}</span></>)}
                    </button>
                    <button type="button" onClick={startRecording} disabled={uploading || disabled} className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50" aria-label={t("mic.rerecord")} title={t("mic.rerecord")}>
                        <Repeat2 className="w-4 h-4" />
                    </button>
                    <button type="button" onClick={discard} disabled={uploading} className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50" aria-label={t("mic.cancel")} title={t("mic.cancel")}>
                        <X className="w-4 h-4" />
                    </button>
                </div>
            ) : (
                <button type="button" onClick={startRecording} disabled={disabled} className="inline-flex items-center justify-center rounded-md border px-3 py-2 hover:bg-gray-50 disabled:opacity-50" aria-label={t("mic.record_audio")} title={t("mic.record_audio")}>
                    <span className="sr-only" />
                    <Mic className="w-4 h-4" />
                </button>
            )}
            {err ? <span className="text-xs text-red-600">{err}</span> : null}
        </div>
    );
}
