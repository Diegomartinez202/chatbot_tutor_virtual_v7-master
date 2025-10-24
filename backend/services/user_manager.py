# =====================================================
# 🧩 backend/services/user_manager.py
# =====================================================
from __future__ import annotations

from typing import Optional, List, Dict, Any

from bson import ObjectId
from passlib.hash import bcrypt
from pymongo.errors import DuplicateKeyError

from backend.db.mongodb import get_database

USERS_COLLECTION = "users"


def _sanitize_user(doc: Dict[str, Any] | None, *, include_password: bool = False) -> Optional[Dict[str, Any]]:
    """
    Convierte _id a str y, por seguridad, elimina password salvo que se solicite explícitamente.
    """
    if not doc:
        return None
    out = dict(doc)
    if "_id" in out and not isinstance(out["_id"], str):
        try:
            out["_id"] = str(out["_id"])
        except Exception:
            out["_id"] = str(out.get("_id"))
    if not include_password:
        out.pop("password", None)
    return out


# 🔹 Crear nuevo usuario
def crear_usuario(email: str, password: str, rol: str = "admin") -> dict:
    db = get_database()
    hashed_password = bcrypt.hash(password)

    usuario = {
        "email": (email or "").strip().lower(),
        "password": hashed_password,
        "rol": rol,
    }

    try:
        result = db[USERS_COLLECTION].insert_one(usuario)
        return {"_id": str(result.inserted_id), "email": usuario["email"], "rol": rol}
    except DuplicateKeyError:
        raise ValueError("El correo ya está registrado")


# 🔹 Buscar usuario por email
def buscar_usuario_por_email(email: str) -> Optional[dict]:
    db = get_database()
    doc = db[USERS_COLLECTION].find_one({"email": (email or "").strip().lower()})
    return _sanitize_user(doc, include_password=True)  # mantener compat para validar_credenciales


# 🔹 Validar credenciales
def validar_credenciales(email: str, password: str) -> Optional[dict]:
    user = buscar_usuario_por_email(email)
    if user and "password" in user and bcrypt.verify(password, user["password"]):
        # devolver sin password
        return _sanitize_user(user, include_password=False)
    return None


# 🔹 Eliminar usuario por email
def eliminar_usuario(email: str) -> bool:
    db = get_database()
    result = db[USERS_COLLECTION].delete_one({"email": (email or "").strip().lower()})
    return result.deleted_count > 0


# 🔹 Listar todos los usuarios (sin password)
def listar_usuarios() -> List[Dict[str, Any]]:
    db = get_database()
    usuarios = db[USERS_COLLECTION].find({}, {"password": 0})
    out: List[Dict[str, Any]] = []
    for user in usuarios:
        s = _sanitize_user(user)
        if s:
            out.append(s)
    return out


# 🔹 Actualizar usuario por ID
def actualizar_usuario(user_id: str, updates: dict) -> dict:
    db = get_database()
    payload = dict(updates or {})

    # Normalización de email
    if "email" in payload and isinstance(payload["email"], str):
        payload["email"] = payload["email"].strip().lower()

    # Re-hash si cambian password
    if "password" in payload and payload["password"]:
        payload["password"] = bcrypt.hash(payload["password"])

    result = db[USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": payload},
    )

    if result.matched_count == 0:
        raise ValueError("No se encontró el usuario")

    # Devolver sin password
    doc = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)}, {"password": 0})
    return _sanitize_user(doc) or {}