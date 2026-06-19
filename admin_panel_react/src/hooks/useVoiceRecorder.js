// src/hooks/useVoiceRecorder.js  (NUEVO)
import { useEffect, useRef, useState } from "react";

export function useVoiceRecorder({ mimeType = "audio/webm" } = {}) {
    const [recording, setRecording] = useState(false);
    const [permission, setPermission] = useState(null);
    const mediaRef = useRef(null);
    const recRef = useRef(null);
    const chunksRef = useRef([]);

    useEffect(() => () => stop(), []); // cleanup

    async function ensurePerm() {
        if (permission != null) return permission;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRef.current = stream;
            setPermission(true);
            return true;
        } catch {
            setPermission(false);
            return false;
        }
    }

    async function start() {
        const ok = await ensurePerm();
        if (!ok) throw new Error("Mic permission denied");
        chunksRef.current = [];
        const rec = new MediaRecorder(mediaRef.current, { mimeType });
        rec.ondataavailable = (e) => e.data && chunksRef.current.push(e.data);
        recRef.current = rec;
        rec.start();
        setRecording(true);
    }

    async function stop() {
        const rec = recRef.current;
        if (!rec) return null;
        if (rec.state !== "inactive") rec.stop();
        await new Promise((r) => setTimeout(r, 50));
        recRef.current = null;
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: mimeType });
        chunksRef.current = [];
        return blob;
    }

    function abort() {
        const rec = recRef.current;
        if (rec && rec.state !== "inactive") rec.stop();
        chunksRef.current = [];
        recRef.current = null;
        setRecording(false);
    }

    return { recording, start, stop, abort, permission };
}
