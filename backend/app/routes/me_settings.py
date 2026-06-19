# backend/routes/me_settings.py
from __future__ import annotations

from typing import Literal, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from backend.dependencies.auth import get_current_user
from backend.db.mongodb import get_user_settings_collection

router = APIRouter(prefix="/api/me", tags=["me"])


# ======== Esquema de preferencias (extensible) ========

class UserSettingsIn(BaseModel):
    language: Literal["es", "en"] = "es"
    theme: Literal["light", "dark"] = "light"
    fontScale: float = Field(1.0, ge=0.75, le=1.5)
    highContrast: bool = False

    @validator("fontScale", pre=True)
    def _coerce_fontscale(cls, v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return 1.0


class UserSettingsOut(UserSettingsIn):
    user_id: str


# ======== Helpers ========

def _normalize_payload(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza claves esperadas y elimina basura.
    Mantén esta función si luego agregas más campos.
    """
    out: Dict[str, Any] = {}
    if "language" in d:
        out["language"] = d["language"] if d["language"] in ("es", "en") else "es"
    if "theme" in d:
        out["theme"] = d["theme"] if d["theme"] in ("light", "dark") else "light"
    if "fontScale" in d:
        try:
            fs = float(d["fontScale"])
            if fs < 0.75:
                fs = 0.75
            if fs > 1.5:
                fs = 1.5
            out["fontScale"] = fs
        except Exception:
            out["fontScale"] = 1.0
    if "highContrast" in d:
        out["highContrast"] = bool(d["highContrast"])
    return out


# ======== Rutas ========

@router.get("/settings", response_model=UserSettingsOut)
async def read_my_settings(user=Depends(get_current_user)):
    """
    Devuelve las preferencias del usuario autenticado.
    Si no existen, retorna defaults sin crear el documento.
    """
    col = get_user_settings_collection()
    doc = col.find_one({"user_id": user["id"]}) or {}
    prefs = {
        "language": doc.get("language", "es"),
        "theme": doc.get("theme", "light"),
        "fontScale": float(doc.get("fontScale", 1.0)),
        "highContrast": bool(doc.get("highContrast", False)),
    }
    return UserSettingsOut(user_id=user["id"], **prefs)


@router.put("/settings")
async def update_my_settings(payload: UserSettingsIn, user=Depends(get_current_user)):
    """
    Upsert de preferencias del usuario autenticado.
    Devuelve { ok: true, prefs: {...} } si todo fue bien.
    """
    col = get_user_settings_collection()
    # Normaliza por si llega con claves extra/invalid
    data = _normalize_payload(payload.dict())

    res = col.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], **data}},
        upsert=True,
    )
    if not (res.acknowledged):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar la configuración",
        )

    return {"ok": True, "prefs": data, "user": {"id": user["id"], "email": user.get("email")}}
