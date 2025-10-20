# backend/routes/admin_auth.py
from __future__ import annotations

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import (
    APIRouter, HTTPException, Depends, Request, Header, Body, Response
)
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
import jwt

# ✅ Rate limiting por endpoint (no-op si SlowAPI no está activo)
from backend.rate_limit import limit

# ─────────────────────────────────────────────────────────────
# Hashing: bcrypt → passlib → error (en ese orden)
# ─────────────────────────────────────────────────────────────
_HASH_IMPL = "none"
try:
    import bcrypt as _bcrypt  # pip install bcrypt
    _HASH_IMPL = "bcrypt"

    def _hash_password(pw: str) -> str:
        return _bcrypt.hashpw(pw.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

    def _verify_password(pw: str, pw_hash: str) -> bool:
        try:
            return _bcrypt.checkpw(pw.encode("utf-8"), pw_hash.encode("utf-8"))
        except Exception:
            return False
except Exception:
    try:
        from passlib.hash import bcrypt as _pbcrypt  # pip install passlib[bcrypt]
        _HASH_IMPL = "passlib"

        def _hash_password(pw: str) -> str:
            return _pbcrypt.hash(pw)

        def _verify_password(pw: str, pw_hash: str) -> bool:
            try:
                return _pbcrypt.verify(pw, pw_hash)
            except Exception:
                return False
    except Exception:
        _HASH_IMPL = "none"

        def _hash_password(pw: str) -> str:  # pragma: no cover
            raise RuntimeError("Instala 'bcrypt' o 'passlib[bcrypt]' para hashing")

        def _verify_password(pw: str, pw_hash: str) -> bool:  # pragma: no cover
            return False

# ─────────────────────────────────────────────────────────────
# Mongo: preferimos helpers; si faltan, fallback PyMongo
# ─────────────────────────────────────────────────────────────
MONGO_URL = (os.getenv("MONGO_URL") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017").strip()
MONGO_DB = (os.getenv("MONGO_DB") or os.getenv("MONGODB_DB") or "chatbot_admin").strip()

_get_db = None
try:
    # Si tienes helpers centralizados, los usamos
    from backend.db.mongodb import get_database, get_users_collection  # type: ignore
    _get_db = get_database

    def _db():
        return get_database()

    def _users():
        return get_users_collection()
except Exception:
    # Fallback
    from pymongo import MongoClient  # type: ignore
    _client = MongoClient(MONGO_URL)
    _fallback_db = _client[MONGO_DB]

    def _db():
        return _fallback_db

    def _users():
        return _fallback_db["users"]

def _col_refresh_tokens():
    return _db()["admin_refresh_tokens"]

def _col_attempts():
    return _db()["auth_attempts"]

def _col_resets():
    return _db()["admin_password_resets"]

# ─────────────────────────────────────────────────────────────
# Loggers/registradores (si existen)
# ─────────────────────────────────────────────────────────────
try:
    from backend.services.auth_service import (  # type: ignore
        registrar_login_exitoso, registrar_acceso_perfil
    )
except Exception:
    def registrar_login_exitoso(request, user): ...
    def registrar_acceso_perfil(request, user): ...

# Dependencia de rol (si existe)
try:
    from backend.dependencies.auth import require_role  # type: ignore
except Exception:
    require_role = None  # fallback manual

# Password policy / security helpers
try:
    from backend.services.password_policy import validate_password  # type: ignore
except Exception:
    def validate_password(p: str):
        # fallback mínima: 8 chars
        ok = len(p) >= int(os.getenv("MIN_PASSWORD_LEN", "8"))
        return ok, ([] if ok else ["La contraseña debe tener al menos 8 caracteres."])

try:
    from backend.services.security import (  # type: ignore
        register_failed_attempt, reset_attempts, is_locked
    )
except Exception:
    # Fallbacks simples sobre la colección auth_attempts
    def register_failed_attempt(email: str, ip: str, lock_minutes: int, max_attempts: int):
        col = _col_attempts()
        now = datetime.now(timezone.utc)
        doc = col.find_one({"email": email})
        if not doc:
            col.insert_one({"email": email, "fail_count": 1, "ip": ip, "lock_until": None, "updated_at": now})
            return
        cnt = int(doc.get("fail_count", 0)) + 1
        lock_until = doc.get("lock_until")
        if cnt >= max_attempts:
            lock_until = now + timedelta(minutes=lock_minutes)
            cnt = 0  # reinicia contador tras bloquear
        col.update_one({"email": email}, {"$set": {"fail_count": cnt, "ip": ip, "lock_until": lock_until, "updated_at": now}})

    def reset_attempts(email: str):
        _col_attempts().update_one({"email": email}, {"$set": {"fail_count": 0, "lock_until": None}})

    def is_locked(email: str) -> bool:
        doc = _col_attempts().find_one({"email": email})
        if not doc:
            return False
        until = doc.get("lock_until")
        if not until:
            return False
        return datetime.now(timezone.utc) < until

# 📌 Prefijo v2 para convivir con tu router legacy en /api/admin
router = APIRouter(prefix="/api/admin2", tags=["admin-auth-v2"])

# ─────────────────────────────────────────────────────────────
# Config JWT & Refresh
# ─────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change_me_please")  # cámbiala en prod
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60")

# Refresh
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "rt")

# Registro abierto solo si lo permites (prod: false)
ADMIN_REGISTRATION_OPEN = os.getenv("ADMIN_REGISTRATION_OPEN", "true").lower() == "true"
FIRST_ADMIN_IS_ADMIN = os.getenv("FIRST_ADMIN_IS_ADMIN", "true").lower() == "true"

# Bloqueos
LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_BLOCK_MINUTES = int(os.getenv("LOGIN_BLOCK_MINUTES", "15"))

# Cookie flags
APP_ENV = os.getenv("APP_ENV", "dev")
COOKIE_SECURE = APP_ENV not in ("dev", "local")
COOKIE_SAMESITE = "lax"

# ─────────────────────────────────────────────────────────────
# Modelos
# ─────────────────────────────────────────────────────────────
class AdminRegisterIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=128)
    accept_terms: bool = Field(True)

class AdminLoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    refresh_token: Optional[str] = None  # se devuelve también por compat

class AdminMeOut(BaseModel):
    id: str
    email: EmailStr
    nombre: Optional[str] = None
    rol: str

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

# ─────────────────────────────────────────────────────────────
# Helpers JWT / Tokens
# ─────────────────────────────────────────────────────────────
def _create_access_token(claims: Dict[str, Any], minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
        **claims,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def _doc_to_out(doc: Dict[str, Any]) -> AdminMeOut:
    return AdminMeOut(
        id=str(doc["_id"]),
        email=doc["email"],
        nombre=doc.get("nombre") or doc.get("name"),
        rol=doc.get("rol") or doc.get("role", "usuario"),
    )

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _issue_refresh(user_id: str) -> str:
    token = secrets.token_urlsafe(48)
    col = _col_refresh_tokens()
    col.insert_one({
        "user_id": ObjectId(user_id),
        "token_hash": _sha256(token),
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "revoked": False,
    })
    # TTL por expires_at (asegurar índice en startup)
    return token

def _rotate_refresh(old_token: Optional[str], user_id: str) -> str:
    if old_token:
        _col_refresh_tokens().update_one(
            {"token_hash": _sha256(old_token), "user_id": ObjectId(user_id)},
            {"$set": {"revoked": True}}
        )
    return _issue_refresh(user_id)

def _fetch_refresh(token: str):
    return _col_refresh_tokens().find_one({"token_hash": _sha256(token), "revoked": False})

def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/",
    )

def _set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        path="/",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

# Fallback auth si no existe require_role
def _decode_bearer(auth_header: Optional[str]) -> Dict[str, Any]:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

def _load_user_by_sub(sub: str) -> Dict[str, Any]:
    try:
        oid = ObjectId(sub)
    except Exception:
        raise HTTPException(status_code=401, detail="Usuario inválido")
    doc = _users().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return doc

async def _current_admin_user(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if require_role:  # usa tu dependencia si existe
        return await require_role(["admin", "soporte"])(request)

    claims = _decode_bearer(authorization)
    sub = claims.get("sub")
    user = _load_user_by_sub(sub)
    rol = user.get("rol") or user.get("role", "usuario")
    if rol not in ("admin", "soporte"):
        raise HTTPException(status_code=403, detail="No autorizado")
    try:
        registrar_acceso_perfil(request, user)
    except Exception:
        pass
    return user

# ─────────────────────────────────────────────────────────────
# Índices
# ─────────────────────────────────────────────────────────────
async def ensure_admin_indexes():
    try:
        _users().create_index("email", name="uniq_email", unique=True)
    except Exception:
        pass
    try:
        _col_refresh_tokens().create_index([("expires_at", 1)], expireAfterSeconds=0, name="ttl_expires_at")
        _col_refresh_tokens().create_index("token_hash", name="token_hash_idx", unique=True)
        _col_refresh_tokens().create_index("user_id", name="user_idx")
    except Exception:
        pass
    try:
        _col_attempts().create_index("email", name="attempts_email_idx", unique=True)
    except Exception:
        pass
    try:
        _col_resets().create_index([("expires_at", 1)], expireAfterSeconds=0, name="ttl_pwresets")
        _col_resets().create_index("token_hash", name="token_hash_pwreset", unique=True)
        _col_resets().create_index("user_id", name="user_pwreset_idx")
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────
# Endpoints (con rate limits por endpoint)
# ─────────────────────────────────────────────────────────────
@router.post("/register")
@limit("5/minute")  # evitar abuso de registro
def admin_register(payload: AdminRegisterIn, request: Request):
    """Crea un usuario para el panel admin/soporte (controlado por ADMIN_REGISTRATION_OPEN)."""
    if not ADMIN_REGISTRATION_OPEN:
        raise HTTPException(status_code=403, detail="Registro deshabilitado por configuración")

    email = payload.email.lower().strip()
    users = _users()

    if users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    ok, errors = validate_password(payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    total = users.estimated_document_count()
    rol = "admin" if (total == 0 and FIRST_ADMIN_IS_ADMIN) else "soporte"

    doc = {
        "nombre": payload.name.strip(),
        "name": payload.name.strip(),  # compat opcional
        "email": email,
        "rol": rol,
        "role": rol,
        "password_hash": _hash_password(payload.password),
        "accept_terms": bool(payload.accept_terms),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "active": True,
    }
    ins = users.insert_one(doc)
    return {"ok": True, "id": str(ins.inserted_id), "message": f"Usuario creado con rol {rol}"}

@router.post("/login", response_model=TokenOut)
@limit("10/minute")  # mitiga fuerza bruta (además de lockouts)
def admin_login(payload: AdminLoginIn, request: Request, response: Response):
    email = payload.email.lower().strip()
    ip = getattr(getattr(request, "state", None), "ip", "") or (request.client.host if request.client else "")

    if is_locked(email):
        raise HTTPException(status_code=429, detail="Cuenta temporalmente bloqueada por intentos fallidos")

    users = _users()
    doc = users.find_one({"email": email})
    if not doc or not _verify_password(payload.password, doc.get("password_hash") or ""):
        register_failed_attempt(email=email, ip=ip, lock_minutes=LOGIN_BLOCK_MINUTES, max_attempts=LOGIN_MAX_ATTEMPTS)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not doc.get("active", True):
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    rol = doc.get("rol") or doc.get("role", "usuario")
    if rol not in ("admin", "soporte"):
        raise HTTPException(status_code=403, detail="No autorizado para panel")

    # éxito → reset de intentos
    reset_attempts(email)

    # tokens
    access = _create_access_token({"sub": str(doc["_id"]), "email": email, "rol": rol})
    refresh = _issue_refresh(str(doc["_id"]))  # ← corregido paréntesis
    _set_refresh_cookie(response, refresh)

    try:
        registrar_login_exitoso(request, doc)
    except Exception:
        pass

    return TokenOut(access_token=access, refresh_token=refresh)

@router.post("/logout")
@limit("60/minute")
def admin_logout(response: Response, refresh_token: Optional[str] = Body(None, embed=True)):
    """Revoca el refresh actual (cookie o body) y limpia cookie."""
    cookie_rt = None
    if refresh_token:
        cookie_rt = refresh_token
    _clear_refresh_cookie(response)
    if cookie_rt:
        _col_refresh_tokens().update_one({"token_hash": _sha256(cookie_rt)}, {"$set": {"revoked": True}})
    return {"ok": True}

@router.get("/refresh", response_model=TokenOut)
@router.post("/refresh", response_model=TokenOut)
@limit("120/minute")  # clientes pueden refrescar token con frecuencia
def admin_refresh(request: Request, response: Response, refresh_token: Optional[str] = Body(None, embed=True)):
    """Entrega nuevo access token; acepta refresh en cookie httpOnly o en body. Rotación activada."""
    token = refresh_token or request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token no presente")

    record = _fetch_refresh(token)
    if not record or record.get("revoked"):
        raise HTTPException(status_code=401, detail="Refresh inválido")

    if record["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh expirado")

    user = _users().find_one({"_id": record["user_id"]})
    if not user or not user.get("active", True):
        raise HTTPException(status_code=401, detail="Usuario inválido/inactivo")

    rol = user.get("rol") or user.get("role", "usuario")
    access = _create_access_token({"sub": str(user["_id"]), "email": user["email"], "rol": rol})
    # Rotación
    new_refresh = _rotate_refresh(token, str(user["_id"]))
    _set_refresh_cookie(response, new_refresh)
    return TokenOut(access_token=access, refresh_token=new_refresh)

@router.get("/me", response_model=AdminMeOut)
@limit("120/minute")
async def admin_me(request: Request, user: Dict[str, Any] = Depends(_current_admin_user)):
    """ Devuelve el perfil del usuario autenticado (admin/soporte). """
    try:
        registrar_acceso_perfil(request, user)
    except Exception:
        pass
    return _doc_to_out(user)

@router.post("/change-password")
@limit("10/minute")
def admin_change_password(
    payload: ChangePasswordIn,
    user: Dict[str, Any] = Depends(_current_admin_user)
):
    if not _verify_password(payload.current_password, user.get("password_hash") or ""):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    ok, errors = validate_password(payload.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    _users().update_one({"_id": user["_id"]}, {"$set": {"password_hash": _hash_password(payload.new_password), "updated_at": datetime.now(timezone.utc)}})
    return {"ok": True, "message": "Contraseña actualizada"}

@router.post("/forgot-password")
@limit("5/minute")
def admin_forgot_password(payload: ForgotPasswordIn):
    """Genera un token de recuperación (placeholder: retornamos el token; en prod → enviar por email)."""
    u = _users().find_one({"email": payload.email.lower().strip()})
    if not u:
        # para no filtrar existencia, devolvemos ok
        return {"ok": True, "message": "Si el correo existe, se enviará un enlace de recuperación"}

    raw = secrets.token_urlsafe(32)
    _col_resets().insert_one({
        "user_id": u["_id"],
        "token_hash": _sha256(raw),
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
    })
    # TODO: enviar email aquí (SMTP configurado en tu settings)
    return {"ok": True, "reset_token": raw}

@router.post("/reset-password")
@limit("5/minute")
def admin_reset_password(payload: ResetPasswordIn):
    rec = _col_resets().find_one({"token_hash": _sha256(payload.token), "used": False})
    if not rec or rec["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    ok, errors = validate_password(payload.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    _users().update_one({"_id": rec["user_id"]}, {"$set": {"password_hash": _hash_password(payload.new_password), "updated_at": datetime.now(timezone.utc)}})
    _col_resets().update_one({"_id": rec["_id"]}, {"$set": {"used": True}})
    # revocar todos los refresh del usuario
    _col_refresh_tokens().update_many({"user_id": rec["user_id"]}, {"$set": {"revoked": True}})
    return {"ok": True, "message": "Contraseña restablecida"}

@router.get("/password-policy")
@limit("120/minute")
def get_policy():
    # snapshot mínimo si no existe el servicio
    try:
        from backend.services.password_policy import policy_snapshot  # type: ignore
        return policy_snapshot()
    except Exception:
        return {"min_length": 8, "requires": ["uppercase", "lowercase", "digit", "special"]}

@router.post("/password-policy/check")
@limit("120/minute")
def check_policy(password: str = Body(..., embed=True), email: Optional[str] = Body(None), name: Optional[str] = Body(None)):
    ok, errors = validate_password(password, email=email, name=name)
    return {"ok": ok, "errors": errors}