# backend/services/user_settings_service.py
from __future__ import annotations

from typing import Optional, Dict, Any
from pymongo.collection import Collection
from pymongo import ASCENDING
from backend.models.user_settings_model import UserSettingsIn, UserSettingsDB


COLLECTION_NAME = "user_settings"


def get_collection(db) -> Collection:
    col = db[COLLECTION_NAME]
    # Índice único para garantizar 1 documento por usuario
    try:
        col.create_index([("user_id", ASCENDING)], unique=True, background=True)
    except Exception:
        pass
    return col


async def get_user_settings(db, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve documento completo (dict) o None si no existe.
    """
    col = get_collection(db)
    doc = col.find_one({"user_id": user_id})
    return doc


async def upsert_user_settings(db, user_id: str, prefs: UserSettingsIn) -> Dict[str, Any]:
    """
    Inserta/actualiza (upsert) las preferencias del usuario.
    Retorna el documento actualizado.
    """
    col = get_collection(db)
    update = {
        "$set": {
            "user_id": user_id,
            "language": prefs.language,
            "theme": prefs.theme,
            "fontScale": float(prefs.fontScale),
            "highContrast": bool(prefs.highContrast),
        }
    }
    col.update_one({"user_id": user_id}, update, upsert=True)
    doc = col.find_one({"user_id": user_id})
    return doc or {
        "user_id": user_id,
        "language": prefs.language,
        "theme": prefs.theme,
        "fontScale": float(prefs.fontScale),
        "highContrast": bool(prefs.highContrast),
    }
