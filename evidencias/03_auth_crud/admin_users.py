# backend/routes/admin_users.py
from __future__ import annotations

from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from bson import ObjectId

from backend.db.mongodb import get_users_collection
from backend.services.password_policy import validate_password

# now_utc fallback (el módulo security puede no exponerlo)
try:
    from backend.services.security import now_utc  # type: ignore
except Exception:
    from datetime import datetime, timezone

    def now_utc():
        return datetime.now(timezone.utc)

# dependencia de rol (si existe)
try:
    from backend.dependencies.auth import require_role  # type: ignore
except Exception:
    require_role = None

# ✅ Rate limiting por endpoint
from backend.rate_limit import limit

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def _users():
    return get_users_collection()


def _objid(uid: str) -> ObjectId:
    try:
        return ObjectId(uid)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")


def _out(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "email": doc.get("email"),
        "nombre": doc.get("nombre") or doc.get("name"),
        "rol": doc.get("rol") or doc.get("role", "usuario"),
        "active": bool(doc.get("active", True)),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "locked_until": doc.get("locked_until"),
        "login_failed_count": int(doc.get("login_failed_count") or 0),
        "token_version": int(doc.get("token_version") or 0),
    }


async def _admin_only(request: Request):
    if require_role:
        return await require_role(["admin"])(request)
    # fallback sencillo
    return True


class RoleIn(BaseModel):
    rol: str = Field(..., pattern="^(admin|soporte|usuario)$")


class StatusIn(BaseModel):
    active: bool


class ResetPasswordIn(BaseModel):
    # si no viene, generamos una temporal
    new_password: Optional[str] = None


@router.get("", dependencies=[Depends(_admin_only)])
@limit("30/minute")  # listado
def list_users(limit: int = 100, offset: int = 0):
    cur = _users().find({}).sort("_id", -1).skip(offset).limit(min(limit, 500))
    return [_out(d) for d in cur]


@router.get("/{user_id}", dependencies=[Depends(_admin_only)])
@limit("30/minute")  # consulta puntual
def get_user(user_id: str):
    d = _users().find_one({"_id": _objid(user_id)})
    if not d:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _out(d)


@router.patch("/{user_id}/role", dependencies=[Depends(_admin_only)])
@limit("10/minute")  # cambio de rol
def change_role(user_id: str, body: RoleIn):
    res = _users().update_one(
        {"_id": _objid(user_id)},
        {"$set": {"rol": body.rol, "role": body.rol, "updated_at": now_utc()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"ok": True}


@router.patch("/{user_id}/status", dependencies=[Depends(_admin_only)])
@limit("10/minute")  # activar/desactivar
def change_status(user_id: str, body: StatusIn):
    res = _users().update_one(
        {"_id": _objid(user_id)},
        {"$set": {"active": bool(body.active), "updated_at": now_utc()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"ok": True}


@router.post("/{user_id}/reset-password", dependencies=[Depends(_admin_only)])
@limit("5/minute")  # sensible
def reset_password(user_id: str, body: ResetPasswordIn):
    # reutilizamos implementación de hash
    from backend.routes.admin_auth import _hash_password  # type: ignore

    new_pw = (body.new_password or "Cambiar123!")
    ok, errors = validate_password(new_pw)
    if not ok:
        raise HTTPException(status_code=400, detail={"password_policy": errors})

    res = _users().update_one(
        {"_id": _objid(user_id)},
        {
            "$set": {"password_hash": _hash_password(new_pw), "updated_at": now_utc()},
            "$inc": {"token_version": 1},
        },
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"ok": True, "temporary_password": new_pw}


@router.post("/{user_id}/revoke", dependencies=[Depends(_admin_only)])
@limit("10/minute")  # revocar sesiones
def revoke_sessions(user_id: str):
    res = _users().update_one(
        {"_id": _objid(user_id)},
        {"$inc": {"token_version": 1}, "$set": {"updated_at": now_utc()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"ok": True}