# backend/routes/me_settings.py
from __future__ import annotations

from typing import Literal, Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, confloat

# ✅ Dependencias del proyecto
from backend.dependencies.auth import get_current_user
from backend.db.mongodb import get_user_settings_collection

router = APIRouter(prefix="/api/me", tags=["me"])


# 🧩 Modelo de preferencias del usuario
class UserSettings(BaseModel):
    language: Literal["es", "en"] = "es"
    theme: Literal["light", "dark"] = "light"
    fontScale: confloat(ge=0.75, le=1.5) = Field(default=1.0)
    highContrast: bool = False


# 🧱 Función interna para formatear documento
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


# 📖 Leer configuración del usuario actual
@router.get("/settings")
def read_my_settings(user=Depends(get_current_user)):
    col = get_user_settings_collection()
    doc = col.find_one({"user_id": user["id"]})

    if not doc:
        # Retorna valores por defecto si el usuario no tiene preferencias guardadas
        return {
            "language": "es",
            "theme": "light",
            "fontScale": 1.0,
            "highContrast": False,
        }

    prefs = doc.get("prefs") or {}
    return {
        "language": prefs.get("language", "es"),
        "theme": prefs.get("theme", "light"),
        "fontScale": float(prefs.get("fontScale", 1.0)),
        "highContrast": bool(prefs.get("highContrast", False)),
    }


# ✏️ Actualizar o crear configuración del usuario
@router.put("/settings")
def update_my_settings(prefs: UserSettings, user=Depends(get_current_user)):
    col = get_user_settings_collection()
    payload = _settings_doc(user["id"], prefs)

    # Upsert (actualiza o crea documento)
    col.update_one(
        {"user_id": user["id"]},
        {"$set": payload},
        upsert=True,
    )

    return {"ok": True, "prefs": payload["prefs"]}
