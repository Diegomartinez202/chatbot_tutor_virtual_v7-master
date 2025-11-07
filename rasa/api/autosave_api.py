# rasa/utils/mongo_autosave.py
from __future__ import annotations
import os, datetime
from typing import Any, Dict
from pymongo import MongoClient

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB   = os.getenv("MONGO_DB", "chatbot_tutor_virtual")
COLL_NAME  = os.getenv("MONGO_AUTOSAVE_COLLECTION", "autosaves")
LOGS_NAME  = os.getenv("MONGO_SECURITY_LOGS_COLLECTION", "seguridad_logs")

_client = MongoClient(MONGO_URI)
_db     = _client[MONGO_DB]
_autos  = _db[COLL_NAME]
_logs   = _db[LOGS_NAME]

def log_event(usuario: str, evento: str, estado: str, detalle: Dict[str, Any] | None = None) -> None:
    _logs.insert_one({
        "usuario": usuario,
        "evento": evento,
        "estado": estado,
        "fecha_hora": datetime.datetime.utcnow(),
        "detalle": detalle or {}
    })

def guardar_autosave(user_id: str, data: Dict[str, Any]) -> None:
    payload = {
        "user_id": user_id,
        "data": data,
        "estado": "guardado",
        "updated_at": datetime.datetime.utcnow(),
    }
    _autos.update_one({"user_id": user_id}, {"$set": payload}, upsert=True)
    log_event(user_id, "autosave_guardar", "ok", {"keys": list(data.keys())})

def cargar_autosave(user_id: str) -> Dict[str, Any] | None:
    doc = _autos.find_one({"user_id": user_id}, {"_id": 0})
    log_event(user_id, "autosave_get", "ok", {"existe": bool(doc)})
    return doc

def eliminar_autosave(user_id: str) -> int:
    res = _autos.delete_one({"user_id": user_id})
    log_event(user_id, "autosave_delete", "ok", {"deleted": res.deleted_count})
    return res.deleted_count
