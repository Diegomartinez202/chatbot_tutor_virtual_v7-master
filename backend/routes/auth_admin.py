# backend/routes/auth_admin.py
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, EmailStr, Field
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.hash import bcrypt
import jwt  # pyjwt

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])

# ────────────────── Config/env ──────────────────
MONGO_URL = (os.getenv("MONGO_URL") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017").strip()
MONGO_DB = (os.getenv("MONGO_DB") or os.getenv("MONGODB_DB") or "chatbot_admin").strip()

SECRET_KEY = os.getenv("SECRET_KEY", "change_me_please")  # ¡pon una fuerte en .env!
JWT_ALG = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60")

# ────────────────── Mongo ──────────────────
_client = AsyncIOMotorClient(MONGO_URL)
_db = _client[MONGO_DB]
_admins = _db["admin_users"]

_indexes_ready = False

async def ensure_admin_indexes():
    """
    Crea índices idempotentes:
    - admin_users: email único
    """
    global _indexes_ready
    if _indexes_ready:
        return
    await _admins.create_index("email", name="uniq_email", unique=True, sparse=False)
    _indexes_ready = True

# ────────────────── Schemas ──────────────────
class RegisterIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    accept_terms: bool = Field(default=False)

class RegisterOut(BaseModel):
    ok: bool
    id: str | None = None
    message: str | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

class AdminMe(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str = "admin"

# ────────────────── Helpers ──────────────────
def _create_access_token(payload: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = payload.copy()
    exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": exp, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALG)

async def _find_admin_by_email(email: str) -> Optional[dict]:
    return await _admins.find_one({"email": email})

# ────────────────── Endpoints ──────────────────
@router.post("/register", response_model=RegisterOut)
@limit("5/minute")  # evitar abuso de registro
async def admin_register(body: RegisterIn = Body(...)):
    await ensure_admin_indexes()

    if not body.accept_terms:
        raise HTTPException(status_code=400, detail="Debes aceptar términos y condiciones.")

    existing = await _find_admin_by_email(body.email.lower())
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo.")

    hashed = bcrypt.hash(body.password)

    doc = {
        "name": body.name.strip(),
        "email": body.email.lower().strip(),
        "password_hash": hashed,
        "role": "admin",
        "created_at": datetime.now(timezone.utc),
        "active": True,
    }
    res = await _admins.insert_one(doc)
    return RegisterOut(ok=True, id=str(res.inserted_id), message="Usuario creado")

@router.post("/login", response_model=TokenOut)
@limit("10/minute")  # mitiga fuerza bruta junto con lockouts externos
async def admin_login(body: LoginIn = Body(...)):
    await ensure_admin_indexes()

    user = await _find_admin_by_email(body.email.lower())
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    if not bcrypt.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    if not user.get("active", True):
        raise HTTPException(status_code=403, detail="Usuario inactivo.")

    token = _create_access_token({"sub": str(user["_id"]), "email": user["email"], "role": user.get("role", "admin")})
    return TokenOut(access_token=token)

# (Opcional) Perfil: útil para /me si lo necesitas luego
from fastapi import Header
from bson import ObjectId

def _decode_token(auth_header: Optional[str]) -> dict:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token requerido.")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido.")

@router.get("/me", response_model=AdminMe)
@limit("120/minute")  # consultas frecuentes al perfil son OK
async def admin_me(authorization: Optional[str] = Header(None)):
    claims = _decode_token(authorization)
    uid = claims.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token inválido.")
    doc = await _admins.find_one({"_id": ObjectId(uid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return AdminMe(id=str(doc["_id"]), name=doc["name"], email=doc["email"], role=doc.get("role", "admin"))