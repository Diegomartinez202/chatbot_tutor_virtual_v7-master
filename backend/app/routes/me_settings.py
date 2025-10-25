# backend/app/routes/me_settings.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
from backend.app.auth.deps import get_current_user

router = APIRouter()

class UserSettings(BaseModel):
    language: Literal["es", "en"] = "es"
    theme: Literal["light", "dark"] = "light"
    fontScale: float = 1.0
    highContrast: bool = False

@router.put("/api/me/settings")
async def update_my_settings(prefs: UserSettings, user=Depends(get_current_user)):
    # TODO: guarda en DB si lo deseas (Mongo/SQL). Por ahora sólo eco:
    return {"ok": True, "user": user["email"], "prefs": prefs.dict()}

@router.get("/api/me/settings")
async def read_my_settings(user=Depends(get_current_user)):
    # TODO: lee desde DB. Defaults por ahora:
    return {"language": "es", "theme": "light", "fontScale": 1.0, "highContrast": False}