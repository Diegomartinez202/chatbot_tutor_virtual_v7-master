# backend/services/user_manager.py

from backend.db.mongodb import get_database
from bson import ObjectId
from passlib.hash import bcrypt
from pymongo.errors import DuplicateKeyError
from typing import Optional

USERS_COLLECTION = "users"

# 🔹 Crear nuevo usuario
def crear_usuario(email: str, password: str, rol: str = "admin") -> dict:
    db = get_database()
    hashed_password = bcrypt.hash(password)

    usuario = {
        "email": email,
        "password": hashed_password,
        "rol": rol
    }

    try:
        result = db[USERS_COLLECTION].insert_one(usuario)
        return {"_id": str(result.inserted_id), "email": email, "rol": rol}
    except DuplicateKeyError:
        raise ValueError("El correo ya está registrado")

# 🔹 Buscar usuario por email
def buscar_usuario_por_email(email: str) -> Optional[dict]:
    db = get_database()
    return db[USERS_COLLECTION].find_one({"email": email})

# 🔹 Validar credenciales
def validar_credenciales(email: str, password: str) -> Optional[dict]:
    user = buscar_usuario_por_email(email)
    if user and bcrypt.verify(password, user["password"]):
        return user
    return None

# 🔹 Eliminar usuario por email
def eliminar_usuario(email: str) -> bool:
    db = get_database()
    result = db[USERS_COLLECTION].delete_one({"email": email})
    return result.deleted_count > 0

# 🔹 Listar todos los usuarios (sin password)
def listar_usuarios() -> list[dict]:
    db = get_database()
    usuarios = db[USERS_COLLECTION].find({}, {"password": 0})
    return [{**user, "_id": str(user["_id"])} for user in usuarios]

# 🔹 Actualizar usuario por ID
def actualizar_usuario(user_id: str, updates: dict) -> dict:
    db = get_database()
    if "password" in updates:
        updates["password"] = bcrypt.hash(updates["password"])

    result = db[USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updates}
    )

    if result.modified_count == 0:
        raise ValueError("No se pudo actualizar el usuario")

    return db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)}, {"password": 0})