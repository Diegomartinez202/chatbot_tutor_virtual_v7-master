# backend/routes/user_settings.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from backend.db.mongodb import get_database
from backend.dependencies.auth import get_current_user
from backend.models.user_settings_model import UserSettingsIn
from backend.services.user_settings_service import get_user_settings, upsert_user_settings

router = APIRouter(prefix="/api/me", tags=["user-settings"])


DEFAULT_PREFS: Dict[str, Any] = {
    "language": "es",
    "theme": "light",
    "fontScale": 1.0,
    "highContrast": False,
}


@router.get("/settings")
async def read_my_settings(user: dict = Depends(get_current_user)):
    """
    Devuelve las preferencias sincronizadas del usuario autenticado.
    Si no existen, devuelve defaults.
    """
    db = get_database()
    doc = await get_user_settings(db, user_id=str(user["id"]))
    if not doc:
        return DEFAULT_PREFS
    return {
        "language": doc.get("language", "es"),
        "theme": doc.get("theme", "light"),
        "fontScale": float(doc.get("fontScale", 1.0)),
        "highContrast": bool(doc.get("highContrast", False)),
    }


@router.put("/settings")
async def update_my_settings(prefs: UserSettingsIn, user: dict = Depends(get_current_user)):
    """
    Guarda/actualiza las preferencias del usuario autenticado.
    """
    db = get_database()
    doc = await upsert_user_settings(db, user_id=str(user["id"]), prefs=prefs)
    if not doc:
        raise HTTPException(status_code=500, detail="No se pudo guardar preferencias")

    return {
        "ok": True,
        "prefs": {
            "language": doc.get("language", "es"),
            "theme": doc.get("theme", "light"),
            "fontScale": float(doc.get("fontScale", 1.0)),
            "highContrast": bool(doc.get("highContrast", False)),
        },
    }
