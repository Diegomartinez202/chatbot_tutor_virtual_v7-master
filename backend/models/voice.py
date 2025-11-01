# backend/models/voice.py
from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class VoiceMeta(BaseModel):
    sender: Optional[str] = Field(default=None, description="ID del usuario/sender del chat")
    lang: Optional[str]   = Field(default="es", description="Idioma esperado")
    stt: Optional[str]    = Field(default="none", description="Proveedor STT (none|whisper|gcloud|... )")
    extra: Optional[Dict[str, Any]] = None

class VoiceSaved(BaseModel):
    id: str
    transcript: Optional[str] = None
    duration_ms: Optional[int] = None
    mime: Optional[str] = None
