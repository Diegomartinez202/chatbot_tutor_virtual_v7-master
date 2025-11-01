# backend/routes/voice.py
from __future__ import annotations
import time
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from bson import ObjectId
from backend.db.mongo import save_audio_bytes, open_audio, get_db
from backend.models.voice import VoiceMeta, VoiceSaved
from backend.services.stt import transcribe_stub

router = APIRouter(prefix="/api/voice", tags=["Voice"])

@router.post("/transcribe", response_model=VoiceSaved)
async def transcribe_voice(
    file: UploadFile = File(..., description="audio/wav, audio/webm, audio/mpeg, etc."),
    sender: Optional[str] = Form(default=None),
    lang: str = Form(default="es"),
    stt: str = Form(default="none"),  # none|whisper|gcloud
):
    try:
        t0 = time.time()
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Archivo vacío")

        meta = VoiceMeta(sender=sender, lang=lang, stt=stt).model_dump()
        file_id = save_audio_bytes(
            raw,
            filename=file.filename or f"voice-{int(t0*1000)}",
            content_type=file.content_type or "application/octet-stream",
            metadata=meta,
        )

        # STT (stub por ahora)
        transcript = transcribe_stub(raw, lang=lang, provider=stt)
        duration_ms = None  # si calculas duración, setéala aquí

        # Guarda un registro mínimo en colección voice_logs (metadatos + ref)
        db = get_db()
        db.voice_logs.insert_one({
            "file_id": ObjectId(file_id),
            "sender": sender,
            "lang": lang,
            "stt": stt,
            "transcript": transcript,
            "duration_ms": duration_ms,
            "content_type": file.content_type,
            "created_at": int(t0 * 1000),
        })

        return VoiceSaved(id=file_id, transcript=transcript, duration_ms=duration_ms, mime=file.content_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {e}")

@router.get("/{id}")
def get_audio(id: str):
    try:
        gridout = open_audio(id)
    except Exception:
        raise HTTPException(status_code=404, detail="Audio no encontrado")

    headers = {
        "Content-Type": gridout.content_type or "application/octet-stream",
        "Content-Length": str(gridout.length),
        "Content-Disposition": f'inline; filename="{gridout.filename or id}"',
    }
    return StreamingResponse(gridout, headers=headers)
