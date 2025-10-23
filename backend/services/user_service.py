from backend.db.mongodb import get_users_collection
from bson import ObjectId
from backend.schemas.user_schema import UserOut
from typing import List, Optional, Dict
from fastapi.responses import StreamingResponse
from io import StringIO
from backend.utils.logging import get_logger
from datetime import datetime
import csv
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# 🧩 UTILIDADES
# ============================================================

def is_valid_object_id(oid: str) -> bool:
    """Valida si un string puede convertirse en ObjectId"""
    valid = ObjectId.is_valid(oid)
    logger.debug(f"Validando ObjectId '{oid}': {valid}")
    return valid


# ============================================================
# 👥 CRUD DE USUARIOS
# ============================================================

def list_users() -> List[UserOut]:
    """Lista todos los usuarios excluyendo las contraseñas"""
    try:
        col = get_users_collection()
        users = col.find({}, {"password": 0})
        result = [UserOut(**{**user, "id": str(user["_id"])}) for user in users]
        logger.info(f"Se listaron {len(result)} usuarios correctamente")
        return result
    except Exception as e:
        logger.error(f"Error al listar usuarios: {str(e)}")
        return []


def delete_user_by_id(user_id: str) -> bool:
    """Elimina un usuario por ID con validación previa"""
    if not is_valid_object_id(user_id):
        logger.warning(f"Intento de eliminar usuario con ID inválido: {user_id}")
        return False
    try:
        col = get_users_collection()
        result = col.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count > 0:
            logger.info(f"Usuario con ID {user_id} eliminado correctamente")
            return True
        logger.warning(f"No se encontró usuario con ID {user_id} para eliminar")
        return False
    except Exception as e:
        logger.error(f"Error al eliminar usuario {user_id}: {str(e)}")
        return False


def find_user_by_email(email: str) -> Optional[Dict]:
    """Busca un usuario por su email"""
    try:
        col = get_users_collection()
        user = col.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
            logger.debug(f"Usuario encontrado por email: {email}")
        else:
            logger.debug(f"No se encontró usuario con email: {email}")
        return user
    except Exception as e:
        logger.error(f"Error buscando usuario por email {email}: {str(e)}")
        return None


# ============================================================
# 🔐 REGISTRO Y AUTENTICACIÓN
# ============================================================

def create_user(nombre: str, email: str, password: str, rol: str = "usuario") -> Dict:
    """
    Crea un nuevo usuario en la base de datos.
    Verifica duplicados, encripta la contraseña y devuelve el usuario creado.
    """
    try:
        col = get_users_collection()

        if find_user_by_email(email):
            logger.warning(f"Intento de registro duplicado: {email}")
            return None

        hashed_password = pwd_context.hash(password)
        user_data = {
            "nombre": nombre.strip(),
            "email": email.strip().lower(),
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
        logger.error(f"Error creando usuario {email}: {str(e)}")
        return None


def crear_usuario_si_no_existe(nombre: str, email: str, password: str, rol: str = "usuario") -> Optional[Dict]:
    """
    Verifica si el usuario ya existe antes de crearlo.
    Si no existe, lo crea y devuelve sus datos.
    Si ya existe, retorna None.
    """
    try:
        existente = find_user_by_email(email)
        if existente:
            logger.info(f"Usuario {email} ya existe, no se crea nuevamente.")
            return None

        nuevo_usuario = create_user(nombre, email, password, rol)
        if nuevo_usuario:
            logger.info(f"Usuario creado exitosamente: {email}")
            return nuevo_usuario
        else:
            logger.warning(f"No se pudo crear usuario {email}")
            return None

    except Exception as e:
        logger.error(f"Error en crear_usuario_si_no_existe: {str(e)}")
        return None


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Autentica un usuario por email y contraseña.
    Devuelve el usuario si la contraseña es correcta, sino None.
    """
    try:
        user = find_user_by_email(email)
        if not user:
            logger.warning(f"Intento de autenticación fallido: usuario {email} no encontrado")
            return None
        hashed_password = user.get("password")
        if not hashed_password:
            logger.warning(f"Usuario {email} no tiene contraseña definida")
            return None
        if pwd_context.verify(password, hashed_password):
            logger.info(f"Usuario {email} autenticado correctamente")
            return user
        logger.warning(f"Contraseña incorrecta para usuario {email}")
        return None
    except Exception as e:
        logger.error(f"Error autenticando usuario {email}: {str(e)}")
        return None


# ============================================================
# 📤 EXPORTACIÓN CSV
# ============================================================

def export_users_csv() -> StreamingResponse:
    """Exporta los usuarios a un archivo CSV descargable"""
    try:
        col = get_users_collection()
        usuarios = col.find({}, {"password": 0})
        usuarios_out = []

        for user in usuarios:
            usuarios_out.append({
                "id": str(user["_id"]),
                "nombre": user.get("nombre", ""),
                "email": user.get("email", ""),
                "rol": user.get("rol", "")
            })

        output = StringIO()
        output.write("\ufeff")  # BOM para Excel UTF-8
        writer = csv.writer(output)
        writer.writerow(["id", "nombre", "email", "rol"])
        for user in usuarios_out:
            writer.writerow([user["id"], user["nombre"], user["email"], user["rol"]])
        output.seek(0)

        filename = f"usuarios_exportados_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        logger.info(f"Usuarios exportados correctamente como {filename}")

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error al exportar usuarios: {str(e)}")
        raise RuntimeError("No se pudo exportar los usuarios") from e