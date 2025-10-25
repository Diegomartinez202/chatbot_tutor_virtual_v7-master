# backend/routes/me_settings.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, conint, confloat
from typing import Literal, Any, Dict
from backend.auth.deps import get_current_user
from backend.db.mongo import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/me", tags=["me"])

class UserSettings(BaseModel):
    language: Literal["es", "en"] = "es"
    theme: Literal["light", "dark"] = "light"
    fontScale: confloat(ge=0.75, le=1.5) = Field(default=1.0)   # límites sanos
    highContrast: bool = False

def _settings_doc(user_id: str, prefs: UserSettings) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "prefs": {
            "language": prefs.language,
            "theme": prefs.theme,
            "fontScale": float(prefs.fontScale),
            "highContrast": bool(prefs.highContrast),
        },
    }

@router.get("/settings")
async def read_my_settings(
    user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    col = db["user_settings"]
    doc = await col.find_one({"user_id": user["id"]})
    if not doc:
        # defaults si el usuario no tiene preferencias guardadas aún
        return {"language": "es", "theme": "light", "fontScale": 1.0, "highContrast": False}
    prefs = doc.get("prefs") or {}
    return {
        "language": prefs.get("language", "es"),
        "theme": prefs.get("theme", "light"),
        "fontScale": float(prefs.get("fontScale", 1.0)),
        "highContrast": bool(prefs.get("highContrast", False)),
    }

@router.put("/settings")
async def update_my_settings(
    prefs: UserSettings,
    user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    col = db["user_settings"]
    payload = _settings_doc(user["id"], prefs)

    # upsert
    await col.update_one(
        {"user_id": user["id"]},
        {"$set": payload},
        upsert=True,
    )
    return {"ok": True, "prefs": payload["prefs"]}