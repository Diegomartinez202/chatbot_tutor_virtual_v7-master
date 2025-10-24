#app/routers/chat_audio.py
from __future__ import annotations

import os
import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from pydantic import BaseModel

import aiohttp
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit
# ✅ Request-ID para trazabilidad extremo a extremo
from backend.middleware.request_id import get_request_id
# ✅ JWT → claims para adjuntar en metadata.auth (si tu middleware/SSO está activo)
from backend.services.jwt_service import decode_token

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
# Rasa REST (fallback directo si no existe app.services.rasa_client)
RASA_REST_URL = os.getenv("RASA_REST_URL", "http://rasa:5005/webhooks/rest/webhook").strip()

# Mongo
MONGO_URL = os.getenv("MONGO_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")).strip()
MONGO_DB = os.getenv("MONGO_DB", os.getenv("MONGODB_DB", "chatbot_admin")).strip()

# Límites y tipos permitidos
MAX_MB = int(os.getenv("MAX_AUDIO_MB", "15"))
MAX_BYTES = MAX_MB * 1024 * 1024
ALLOWED_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/wav",
    "audio/mp4",
    "audio/x-m4a",
}

# GridFS opcional
GRIDFS_ENABLED = (os.getenv("GRIDFS_ENABLED", "false").lower() == "true")

# TTL para referencias de audio si guardas URL/ID externo
AUDIO_TTL_DAYS = int(os.getenv("AUDIO_TTL_DAYS", "7"))

# ─────────────────────────────────────────────────────────────
# Mongo client & colecciones
# ─────────────────────────────────────────────────────────────
_client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
_db = _client[MONGO_DB]
_voice_logs = _db["voice_logs"]                     # logs permanentes (no TTL)
_voice_audio_refs = _db["voice_audio_refs"]         # refs a binario (TTL por expires_at)
_messages = _db["messages"]                         # opcional (histórico compacto)

# GridFS bucket (opcional)
_fs_bucket = None
if GRIDFS_ENABLED:
    try:
        _fs_bucket = motor.motor_asyncio.AsyncIOMotorGridFSBucket(_db, bucket_name="uploads")
    except Exception:
        _fs_bucket = None

_indexes_ready = False
_indexes_lock = asyncio.Lock()

async def ensure_indexes():
    """
    Crea índices idempotentes:
      - voice_logs: created_at desc
      - voice_audio_refs: TTL por expires_at
      - messages: created_at desc
    """
    global _indexes_ready
    if _indexes_ready:
        return

    async with _indexes_lock:
        if _indexes_ready:
            return

        await _voice_logs.create_index([("created_at", -1)], name="created_at_desc")
        await _voice_audio_refs.create_index(
            [("expires_at", 1)],
            expireAfterSeconds=0,
            name="ttl_expires_at",
        )
        await _messages.create_index([("created_at", -1)], name="created_at_desc")

        _indexes_ready = True


# ─────────────────────────────────────────────────────────────
# STT: usa servicio si existe, si no fallback stub
# ─────────────────────────────────────────────────────────────
async def _transcribe(blob: bytes, mime: str, lang: str, tmp_path: Optional[str]) -> Dict[str, Any]:
    """
    Retorna dict con shape:
      { "text": str, "engine": "stub|...", "lang": str, "confidence": Optional[float] }
    """
    # 1) Intentar servicio real si existe
    try:
        from app.services.stt import transcribe_audio  # type: ignore
        stt = await transcribe_audio(blob, mime, lang=lang)
        text = (stt.get("text") or "").strip()
        if text:
            return {
                "text": text,
                "engine": stt.get("engine") or "custom",
                "lang": stt.get("lang") or lang,
                "confidence": stt.get("confidence"),
                **{k: v for k, v in stt.items() if k not in {"text", "engine", "lang", "confidence"}},
            }
    except Exception:
        # Si falla el import o el servicio, continuamos al stub
        pass

    # 2) Stub (placeholder). Si quieres usar tmp_path con Whisper, aquí es el lugar.
    text = "(transcripción simulada) hola, necesito ayuda con fracciones"
    return {"text": text, "engine": "stub", "lang": lang, "confidence": None}


# ─────────────────────────────────────────────────────────────
# Rasa REST: usa cliente si existe, si no HTTP directo
# ─────────────────────────────────────────────────────────────
async def _send_to_rasa(sender: str, message: str, metadata: Dict[str, Any], request_id: Optional[str] = None) -> Any:
    # 1) Cliente propio si existe
    try:
        from app.services.rasa_client import send_to_rasa  # type: ignore
        # Idealmente tu cliente ya propaga X-Request-ID internamente
        return await send_to_rasa(sender=sender, message=message, metadata=metadata)
    except Exception:
        pass

    # 2) Fallback HTTP directo
    headers = {"Content-Type": "application/json"}
    if request_id:
        headers["X-Request-ID"] = request_id

    async with aiohttp.ClientSession() as s:
        async with s.post(
            RASA_REST_URL,
            json={"sender": sender, "message": message, "metadata": metadata},
            headers=headers,
            timeout=30,
        ) as r:
            r.raise_for_status()
            return await r.json()


# ─────────────────────────────────────────────────────────────
# Modelos de respuesta
# ─────────────────────────────────────────────────────────────
class AudioInfo(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    mime: Optional[str] = None
    size_bytes: Optional[int] = None

class ChatAudioResponse(BaseModel):
    ok: bool
    transcript: str
    audio: Optional[AudioInfo] = None
    rasa: Any


# ─────────────────────────────────────────────────────────────
# Endpoint principal
# ─────────────────────────────────────────────────────────────
@router.post("/audio", response_model=ChatAudioResponse)
@limit("15/minute")  # subidas de audio controladas
async def post_chat_audio(
    request: Request,
    # Soportamos ambos nombres: file | audio (para compatibilidad con clientes)
    file: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    lang: str = Form("es"),
    persona: Optional[str] = Form(None),
    user_id: str = Form("anon"),
    session_id: Optional[str] = Form(None),
):
    up: UploadFile | None = file or audio
    if up is None:
        raise HTTPException(status_code=400, detail="Falta el archivo de audio (file|audio).")

    mime = (up.content_type or "").lower()
    if mime not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Tipo no permitido: {mime}")

    blob = await up.read()
    size_bytes = len(blob)
    if size_bytes > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"Audio demasiado grande (>{MAX_MB}MB)")

    # Archivo temporal (por si algún STT lo requiere)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            tmp.write(blob)
            tmp_path = tmp.name
    except Exception:
        tmp_path = None

    # ── 1) STT ───────────────────────────────────────────────
    stt = await _transcribe(blob=blob, mime=mime, lang=lang, tmp_path=tmp_path)
    transcript = (stt.get("text") or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="No se obtuvo transcripción.")

    # ── 2) Guardar binario opcional (GridFS) ─────────────────
    audio_id_str: Optional[str] = None
    audio_url: Optional[str] = None
    if GRIDFS_ENABLED and _fs_bucket is not None:
        try:
            fid = await _fs_bucket.upload_from_stream(up.filename or "audio.bin", blob, metadata={"mime": mime})
            audio_id_str = str(fid)
            # Ruta interna; expón un media router si quieres servir binarios
            audio_url = f"/api/media/{audio_id_str}"
        except Exception:
            audio_id_str = None
            audio_url = None

    # ── 3) Auth → claims para metadata.auth ──────────────────
    auth_header = request.headers.get("Authorization")
    is_valid, claims = decode_token(auth_header)

    # ── 4) Enviar a Rasa ─────────────────────────────────────
    sender = user_id or session_id or "anon"
    rid = get_request_id()  # trazabilidad
    metadata = {
        "persona": persona,
        "lang": lang,
        "via": "audio",
        "audio": {"id": audio_id_str, "url": audio_url, "mime": mime, "size_bytes": size_bytes},
        "stt": stt,
        "auth": {"hasToken": bool(is_valid), "claims": claims if is_valid else {}},
        # contexto útil de red
        "net": {
            "ip": getattr(request.state, "ip", None) or (request.client.host if request.client else None),
            "user_agent": getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
            "request_id": rid,
        },
    }
    rasa_resp = await _send_to_rasa(
        sender=sender,
        message=transcript or "[audio sin transcripción]",
        metadata=metadata,
        request_id=rid
    )

    # ── 5) Logs Mongo ────────────────────────────────────────
    await ensure_indexes()
    now = datetime.now(timezone.utc)

    try:
        await _voice_logs.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "transcript": transcript,
            "stt": stt,
            "mime": mime,
            "size_bytes": size_bytes,
            "created_at": now,
            "rasa_preview": rasa_resp[0] if isinstance(rasa_resp, list) and rasa_resp else rasa_resp,
            "error": None,
            # enriquecimiento de auditoría
            "ip": getattr(request.state, "ip", None) or (request.client.host if request.client else None),
            "user_agent": getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
            "request_id": rid,
        })
    except Exception:
        pass

    # Guardar referencia con TTL (si quieres limpiar a la semana)
    if audio_id_str or audio_url:
        try:
            await _voice_audio_refs.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "audio": {
                    "id": ObjectId(audio_id_str) if (audio_id_str and ObjectId.is_valid(audio_id_str)) else audio_id_str,
                    "url": audio_url,
                    "mime": mime,
                    "size_bytes": size_bytes,
                },
                "created_at": now,
                "expires_at": now + timedelta(days=AUDIO_TTL_DAYS),
            })
        except Exception:
            pass

    # (Opcional) persistir en messages
    try:
        await _messages.insert_one({
            "user_id": user_id,
            "conversation_id": sender,
            "role": "user",
            "kind": "audio",
            "text": transcript,
            "audio": {"id": audio_id_str, "url": audio_url, "mime": mime, "size_bytes": size_bytes},
            "stt": stt,
            "created_at": datetime.utcnow(),
            "request_id": rid,
        })
    except Exception:
        pass

    # Limpieza del temporal
    if tmp_path:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    return ChatAudioResponse(
        ok=True,
        transcript=transcript,
        audio=AudioInfo(id=audio_id_str, url=audio_url, mime=mime, size_bytes=size_bytes),
        rasa=rasa_resp,
    )