# backend/services/user_service.py
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from io import StringIO
import csv

from bson import ObjectId
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from fastapi.responses import StreamingResponse

from backend.db.mongodb import get_users_collection
from backend.schemas.user_schema import UserOut
from backend.utils.logging import get_logger

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# Utilidades
# ============================================================

def is_valid_object_id(oid: str) -> bool:
    """Valida si un string puede convertirse en ObjectId."""
    valid = ObjectId.is_valid(oid)
    logger.debug(f"Validando ObjectId '{oid}': {valid}")
    return valid


# ============================================================
# Consultas básicas
# ============================================================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su email (devuelve dict con _id como str)."""
    try:
        col = get_users_collection()
        user = col.find_one({"email": (email or "").strip().lower()})
        if user:
            user["_id"] = str(user["_id"])
            logger.debug(f"Usuario encontrado por email: {email}")
        else:
            logger.debug(f"No se encontró usuario con email: {email}")
        return user
    except Exception as e:
        logger.error(f"Error buscando usuario por email {email}: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su _id (string)."""
    if not is_valid_object_id(user_id):
        logger.warning(f"ID inválido al buscar usuario: {user_id}")
        return None
    try:
        col = get_users_collection()
        user = col.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            logger.debug(f"Usuario encontrado por id: {user_id}")
        else:
            logger.debug(f"No se encontró usuario con id: {user_id}")
        return user
    except Exception as e:
        logger.error(f"Error buscando usuario por id {user_id}: {e}")
        return None


# ============================================================
# CRUD de usuarios
# ============================================================

def list_users() -> List[UserOut]:
    """Lista todos los usuarios excluyendo las contraseñas."""
    try:
        col = get_users_collection()
        users = col.find({}, {"password": 0})
        result = [UserOut(**{**u, "id": str(u["_id"])}) for u in users]
        logger.info(f"Se listaron {len(result)} usuarios correctamente")
        return result
    except Exception as e:
        logger.error(f"Error al listar usuarios: {e}")
        return []


def get_users() -> List[UserOut]:
    """
    En algunos controladores se importa get_users (en lugar de list_users).
    Devolvemos exactamente lo mismo que list_users sin alias raros.
    """
    return list_users()


def create_user(nombre: str, email: str, password: str, rol: str = "usuario") -> Optional[Dict[str, Any]]:
    """
    Crea un nuevo usuario en la base de datos.
    Verifica duplicados, encripta la contraseña y devuelve el usuario creado.
    """
    try:
        col = get_users_collection()

        if get_user_by_email(email):
            logger.warning(f"Intento de registro duplicado: {email}")
            return None

        hashed_password = pwd_context.hash(password)
        user_data: Dict[str, Any] = {
            "nombre": (nombre or "").strip(),
            "email": (email or "").strip().lower(),
            "password": hashed_password,
            "rol": rol,
            "fecha_registro": datetime.utcnow(),
        }

        result = col.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        logger.info(f"Nuevo usuario registrado correctamente: {email}")
        return user_data

    except DuplicateKeyError:
        logger.warning(f"Correo duplicado detectado: {email}")
        return None
    except Exception as e:
        logger.error(f"Error creando usuario {email}: {e}")
        return None


def update_user(user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza campos básicos del usuario.
    - Permite: nombre, email, rol, password (se re-hash).
    - Valida duplicado de email si viene en la actualización.
    Devuelve el usuario actualizado (sin password) o None.
    """
    if not is_valid_object_id(user_id):
        logger.warning(f"ID inválido al actualizar usuario: {user_id}")
        return None

    try:
        allowed_fields = {"nombre", "email", "rol", "password"}
        payload = {k: v for k, v in (data or {}).items() if k in allowed_fields}

        if "email" in payload and payload["email"]:
            payload["email"] = str(payload["email"]).strip().lower()
            # comprobar duplicado con otro _id
            col = get_users_collection()
            dup = col.find_one({"email": payload["email"], "_id": {"$ne": ObjectId(user_id)}})
            if dup:
                logger.warning(f"Actualización rechazada por email duplicado: {payload['email']}")
                return None

        if "password" in payload and payload["password"]:
            payload["password"] = pwd_context.hash(str(payload["password"]))

        if not payload:
            logger.info(f"Sin cambios para el usuario {user_id}")
            return get_user_by_id(user_id)

        col = get_users_collection()
        res = col.update_one({"_id": ObjectId(user_id)}, {"$set": payload})
        if res.matched_count == 0:
            logger.warning(f"No se encontró usuario para actualizar: {user_id}")
            return None

        # devolver actualizado
        updated = col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if updated:
            updated["_id"] = str(updated["_id"])
        logger.info(f"Usuario {user_id} actualizado correctamente")
        return updated

    except Exception as e:
        logger.error(f"Error actualizando usuario {user_id}: {e}")
        return None


def delete_user_by_id(user_id: str) -> bool:
    """Elimina un usuario por ID con validación previa."""
    if not is_valid_object_id(user_id):
        logger.warning(f"Intento de eliminar usuario con ID inválido: {user_id}")
        return False
    try:
        col = get_users_collection()
        res = col.delete_one({"_id": ObjectId(user_id)})
        if res.deleted_count > 0:
            logger.info(f"Usuario con ID {user_id} eliminado correctamente")
            return True
        logger.warning(f"No se encontró usuario con ID {user_id} para eliminar")
        return False
    except Exception as e:
        logger.error(f"Error al eliminar usuario {user_id}: {e}")
        return False


# ============================================================
# Autenticación
# ============================================================

def verify_user_credentials(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verifica credenciales (email + password).
    Devuelve el usuario si la contraseña es correcta; si no, None.
    """
    try:
        user = get_user_by_email(email)
        if not user:
            logger.warning(f"Login fallido: usuario {email} no encontrado")
            return None
        hashed = user.get("password")
        if not hashed:
            logger.warning(f"Usuario {email} sin contraseña definida")
            return None
        if pwd_context.verify(password, hashed):
            logger.info(f"Usuario {email} autenticado correctamente")
            return user
        logger.warning(f"Contraseña incorrecta para usuario {email}")
        return None
    except Exception as e:
        logger.error(f"Error verificando credenciales de {email}: {e}")
        return None


# ============================================================
# Exportación CSV
# ============================================================

def export_users_csv() -> StreamingResponse:
    """Exporta los usuarios a CSV (sin contraseñas)."""
    try:
        col = get_users_collection()
        users = col.find({}, {"password": 0})

        rows: List[Dict[str, str]] = []
        for u in users:
            rows.append({
                "id": str(u["_id"]),
                "nombre": u.get("nombre", "") or "",
                "email": u.get("email", "") or "",
                "rol": u.get("rol", "") or "",
            })

        output = StringIO()
        # BOM para Excel UTF-8
        output.write("\ufeff")
        writer = csv.writer(output)
        writer.writerow(["id", "nombre", "email", "rol"])
        for r in rows:
            writer.writerow([r["id"], r["nombre"], r["email"], r["rol"]])
        output.seek(0)

        filename = f"usuarios_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        logger.info(f"Usuarios exportados correctamente como {filename}")

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error al exportar usuarios: {e}")
        raise RuntimeError("No se pudo exportar los usuarios") from e