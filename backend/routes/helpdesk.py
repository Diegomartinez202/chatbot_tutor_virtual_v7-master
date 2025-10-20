# backend/routes/helpdesk.py
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from bson.objectid import ObjectId
from pymongo import MongoClient

from backend.config.settings import settings

# ✅ Rate limiting por endpoint
from backend.rate_limit import limit

router = APIRouter(prefix="/api/helpdesk", tags=["helpdesk"])


# --- Modelos de entrada/salida ---
class TicketIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    subject: str = Field(..., min_length=2, max_length=180)
    message: str = Field(..., min_length=2, max_length=5000)
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _get_db():
    client = MongoClient(settings.mongo_uri)
    return client[settings.mongo_db_name]


def _check_auth(request: Request):
    """Si HELPDESK_TOKEN está definido, exigimos Authorization: Bearer <token>"""
    required = (settings.helpdesk_token or "").strip()
    if not required:
        return  # sin token → endpoint abierto (útil en dev)
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    token = auth.split(" ", 1)[1].strip()
    if token != required:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")


@router.get("/health")
async def helpdesk_health():
    return {"ok": True, "kind": settings.helpdesk_kind, "webhook": settings.helpdesk_webhook or "internal"}


@router.post("/tickets")
@limit("5/minute")  # ⛳ evita spam de creación de tickets
async def create_ticket(payload: TicketIn, request: Request):
    _check_auth(request)

    db = _get_db()
    now = datetime.now(timezone.utc)

    doc = {
        "name": payload.name,
        "email": payload.email,
        "subject": payload.subject,
        "message": payload.message,
        "conversation_id": payload.conversation_id,
        "metadata": payload.metadata or {},
        "status": "open",
        "source": "webhook",  # origen genérico
        # contexto útil
        "ip": getattr(request.state, "ip", None) or request.client.host,
        "user_agent": getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
        "created_at": now,
        "updated_at": now,
    }

    res = db.helpdesk_tickets.insert_one(doc)
    ticket_id = str(res.inserted_id)

    return {
        "ok": True,
        "ticket_id": ticket_id,
        "message": "Ticket creado correctamente.",
    }