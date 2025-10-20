# backend/routes/user.py
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional

from backend.dependencies.auth import require_role
from backend.schemas.user_schema import UserCreate, UserOut
from backend.services.user_manager import crear_usuario
from backend.services.user_service import list_users, delete_user_by_id, export_users_csv
from backend.services.log_service import log_access

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter(tags=["Usuarios"])

def _ip(request: Request) -> str:
    return getattr(request.state, "ip", None) or (request.client.host if request.client else "unknown")

def _ua(request: Request) -> str:
    return getattr(request.state, "user_agent", None) or request.headers.get("user-agent", "")

# 🔹 1. Listar usuarios (admin y soporte)
@router.get("/admin/users", summary="Listar usuarios registrados", response_model=List[UserOut])
@limit("30/minute")  # consultas más frecuentes
def list_users_route(request: Request, payload=Depends(require_role(["admin", "soporte"]))):
    users = list_users()

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/users",
        method="GET",
        status=200 if users else 204,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return users

# 🔹 2. Eliminar usuario por ID (solo admin)
@router.delete("/admin/users/{user_id}", summary="Eliminar usuario por ID")
@limit("10/minute")  # operación sensible
def delete_user_route(user_id: str, request: Request, payload=Depends(require_role(["admin"]))):
    success = delete_user_by_id(user_id)

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint=f"/admin/users/{user_id}",
        method="DELETE",
        status=200 if success else 404,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"message": "🗑️ Usuario eliminado correctamente"}

# 🔹 3. Exportar usuarios a CSV (solo admin)
@router.get("/admin/users/export", summary="Exportar usuarios a CSV", response_class=StreamingResponse)
@limit("10/minute")  # export es costoso
def exportar_usuarios_csv_route(request: Request, payload=Depends(require_role(["admin"]))):
    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/users/export",
        method="GET",
        status=200,
        ip=_ip(request),
        user_agent=_ua(request),
    )

    return export_users_csv()

# 🔐 4. Crear usuario desde el panel (solo admin)
@router.post("/admin/create-user", summary="Crear nuevo usuario", response_model=UserOut)
@limit("10/minute")  # creación controlada
def create_user_admin(
    request: Request,
    user: UserCreate = Body(...),
    payload=Depends(require_role(["admin"]))
):
    try:
        nuevo_usuario = crear_usuario(user.email, user.password, user.rol)

        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint="/admin/create-user",
            method="POST",
            status=201,
            ip=_ip(request),
            user_agent=_ua(request),
        )

        # Compat: si UserOut espera 'nombre' y no viene de la DB, usamos el del payload si existe
        nombre: Optional[str] = getattr(user, "nombre", None)

        return UserOut(
            id=str(nuevo_usuario.get("_id", "")),
            email=nuevo_usuario["email"],
            nombre=nombre,
            rol=nuevo_usuario["rol"],
        )

    except ValueError as e:
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint="/admin/create-user",
            method="POST",
            status=400,
            ip=_ip(request),
            user_agent=_ua(request),
        )
        raise HTTPException(status_code=400, detail=str(e))