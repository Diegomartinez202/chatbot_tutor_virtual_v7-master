# =====================================================
# 🧩 backend/services/user_service.py
# =====================================================
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


# =====================================================
# Utilidades
# =====================================================
def is_valid_object_id(oid: str) -> bool:
    """Valida si un string puede convertirse en ObjectId."""
    valid = ObjectId.is_valid(oid)
    logger.debug(f"[users] Validando ObjectId '{oid}': {valid}")
    return valid


def _norm_email(email: str) -> str:
    """Normaliza email a minúsculas y sin espacios."""
    return (email or "").strip().lower()


def _to_public_user(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte un documento Mongo a un dict público:
    - _id -> id (str)
    - oculta password si viniera por error
    """
    if not doc:
        return {}
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out["_id"])
        out.pop("_id", None)
    out.pop("password", None)
    return out


# =====================================================
# Consultas básicas
# =====================================================
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su email (devuelve dict con id como str)."""
    try:
        col = get_users_collection()
        user = col.find_one({"email": _norm_email(email)})
        if user:
            user = _to_public_user(user)
            logger.debug(f"[users] Usuario encontrado por email: {email}")
        else:
            logger.debug(f"[users] No se encontró usuario con email: {email}")
        return user
    except Exception as e:
        logger.error(f"[users] Error buscando usuario por email {email}: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un usuario por su _id (string)."""
    if not is_valid_object_id(user_id):
        logger.warning(f"[users] ID inválido al buscar usuario: {user_id}")
        return None
    try:
        col = get_users_collection()
        user = col.find_one({"_id": ObjectId(user_id)})
        if user:
            user = _to_public_user(user)
            logger.debug(f"[users] Usuario encontrado por id: {user_id}")
        else:
            logger.debug(f"[users] No se encontró usuario con id: {user_id}")
        return user
    except Exception as e:
        logger.error(f"[users] Error buscando usuario por id {user_id}: {e}")
        return None


# =====================================================
# CRUD de usuarios
# =====================================================
def list_users() -> List[UserOut]:
    """Lista todos los usuarios excluyendo las contraseñas."""
    try:
        col = get_users_collection()
        # Excluimos password por proyección
        users_cur = col.find({}, {"password": 0})
        result: List[UserOut] = []
        for u in users_cur:
            pub = _to_public_user(u)
            # UserOut espera 'id' (str) y no '_id'
            result.append(UserOut(**pub))
        logger.info(f"[users] Se listaron {len(result)} usuarios correctamente")
        return result
    except Exception as e:
        logger.error(f"[users] Error al listar usuarios: {e}")
        return []


def get_users() -> List[UserOut]:
    """
    Algunos controladores importan get_users.
    Devuelve exactamente lo mismo que list_users.
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
            logger.warning(f"[users] Intento de registro duplicado: {email}")
            return None

        hashed_password = pwd_context.hash(password)
        user_data: Dict[str, Any] = {
            "nombre": (nombre or "").strip(),
            "email": _norm_email(email),
            "password": hashed_password,
            "rol": rol,
            "fecha_registro": datetime.utcnow(),
        }

        result = col.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        pub = _to_public_user(user_data)
        logger.info(f"[users] Nuevo usuario registrado correctamente: {pub.get('email')}")
        return pub

    except DuplicateKeyError:
        logger.warning(f"[users] Correo duplicado detectado: {email}")
        return None
    except Exception as e:
        logger.error(f"[users] Error creando usuario {email}: {e}")
        return None


def crear_usuario_si_no_existe(nombre: str, email: str, password: str, rol: str = "usuario") -> Optional[Dict[str, Any]]:
    """
    Si el usuario ya existe (por email), no lo crea y devuelve None.
    Si no existe, lo crea y devuelve sus datos.
    """
    try:
        email_norm = _norm_email(email)
        existente = get_user_by_email(email_norm)
        if existente:
            logger.info(f"[users] Usuario {email_norm} ya existe, no se crea nuevamente.")
            return None

        nuevo = create_user(nombre=nombre, email=email_norm, password=password, rol=rol)
        if nuevo:
            logger.info(f"[users] Usuario creado exitosamente: {email_norm}")
            return nuevo

        logger.warning(f"[users] No se pudo crear usuario {email_norm}")
        return None

    except Exception as e:
        logger.error(f"[users] Error en crear_usuario_si_no_existe({email}): {e}")
        return None


def update_user(user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza campos básicos del usuario.
    - Permite: nombre, email, rol, password (se re-hash).
    - Valida duplicado de email si viene en la actualización.
    Devuelve el usuario actualizado (sin password) o None.
    """
    if not is_valid_object_id(user_id):
        logger.warning(f"[users] ID inválido al actualizar usuario: {user_id}")
        return None

    try:
        allowed_fields = {"nombre", "email", "rol", "password"}
        payload = {k: v for k, v in (data or {}).items() if k in allowed_fields}

        if "email" in payload and payload["email"]:
            payload["email"] = _norm_email(payload["email"])
            col = get_users_collection()
            dup = col.find_one({"email": payload["email"], "_id": {"$ne": ObjectId(user_id)}})
            if dup:
                logger.warning(f"[users] Actualización rechazada por email duplicado: {payload['email']}")
                return None

        if "password" in payload and payload["password"]:
            payload["password"] = pwd_context.hash(str(payload["password"]))

        col = get_users_collection()
        if not payload:
            logger.info(f"[users] Sin cambios para el usuario {user_id}")
            u = col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
            return _to_public_user(u) if u else None

        res = col.update_one({"_id": ObjectId(user_id)}, {"$set": payload})
        if res.matched_count == 0:
            logger.warning(f"[users] No se encontró usuario para actualizar: {user_id}")
            return None

        updated = col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        pub = _to_public_user(updated) if updated else None
        logger.info(f"[users] Usuario {user_id} actualizado correctamente")
        return pub

    except Exception as e:
        logger.error(f"[users] Error actualizando usuario {user_id}: {e}")
        return None


def delete_user_by_id(user_id: str) -> bool:
    """Elimina un usuario por ID con validación previa."""
    if not is_valid_object_id(user_id):
        logger.warning(f"[users] Intento de eliminar usuario con ID inválido: {user_id}")
        return False
    try:
        col = get_users_collection()
        res = col.delete_one({"_id": ObjectId(user_id)})
        if res.deleted_count > 0:
            logger.info(f"[users] Usuario con ID {user_id} eliminado correctamente")
            return True
        logger.warning(f"[users] No se encontró usuario con ID {user_id} para eliminar")
        return False
    except Exception as e:
        logger.error(f"[users] Error al eliminar usuario {user_id}: {e}")
        return False


# =====================================================
# Autenticación
# =====================================================
def verify_user_credentials(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verifica credenciales (email + password).
    Devuelve el usuario si la contraseña es correcta; si no, None.
    """
    try:
        email_norm = _norm_email(email)
        col = get_users_collection()
        # Traemos password solo aquí porque necesitamos verificarlo
        user = col.find_one({"email": email_norm})
        if not user:
            logger.warning(f"[auth] Login fallido: usuario {email_norm} no encontrado")
            return None
        hashed = user.get("password")
        if not hashed:
            logger.warning(f"[auth] Usuario {email_norm} sin contraseña definida")
            return None
        if pwd_context.verify(password, hashed):
            logger.info(f"[auth] Usuario {email_norm} autenticado correctamente")
            return _to_public_user(user) | {"password": hashed}  # conservamos compat si alguien lee el hash
        logger.warning(f"[auth] Contraseña incorrecta para usuario {email_norm}")
        return None
    except Exception as e:
        logger.error(f"[auth] Error verificando credenciales de {email}: {e}")
        return None


# =====================================================
# Exportación CSV
# =====================================================
def export_users_csv() -> StreamingResponse:
    """Exporta los usuarios a CSV (sin contraseñas)."""
    try:
        col = get_users_collection()
        users = col.find({}, {"password": 0})

        rows: List[Dict[str, str]] = []
        for u in users:
            pub = _to_public_user(u)
            rows.append({
                "id": pub.get("id", ""),
                "nombre": pub.get("nombre", "") or "",
                "email": pub.get("email", "") or "",
                "rol": pub.get("rol", "") or "",
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
        logger.info(f"[users] Usuarios exportados correctamente como {filename}")

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"[users] Error al exportar usuarios: {e}")
        raise RuntimeError("No se pudo exportar los usuarios") from e


# =====================================================
# (Opcional) Índices recomendados
# =====================================================
def ensure_users_indexes() -> None:
    """
    Crea índices recomendados. No se invoca automáticamente para no
    tocar tu flujo; si quieres, llámalo en startup.
    """
    try:
        col = get_users_collection()
        col.create_index("email", unique=True, name="uniq_email")
        logger.info("[users] Índices verificados/creados (email único).")
    except Exception as e:
        logger.warning(f"[users] No fue posible crear índices sugeridos: {e}")
