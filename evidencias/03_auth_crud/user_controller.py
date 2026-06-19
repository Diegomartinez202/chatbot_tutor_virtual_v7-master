# backend/routes/user_controller.py

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.responses import StreamingResponse
from typing import List

from backend.dependencies.auth import require_role
from backend.schemas.user_schema import UserCreate, UserOut
from backend.services.user_manager import crear_usuario
from backend.services.user_service import list_users, delete_user_by_id, export_users_csv
from backend.services.log_service import log_access

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit

router = APIRouter(tags=["Usuarios"])

# 🔹 1. Listar usuarios (admin y soporte)
@router.get(
    "/admin/users",
    summary="Listar usuarios registrados",
    response_model=List[UserOut],
)
@limit("30/minute")  # consultas de listado (moderado)
def list_users_route(
    request: Request,
    payload=Depends(require_role(["admin", "soporte"]))
):
    users = list_users()

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/users",
        method="GET",
        status=200 if users else 204,
        ip=getattr(request.state, "ip", None) or (request.client.host if request.client else None),
        user_agent=getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
    )

    return users

# 🔹 2. Eliminar usuario por ID (solo admin)
@router.delete("/admin/users/{user_id}", summary="Eliminar usuario por ID")
@limit("10/minute")  # operaciones destructivas (más estricto)
def delete_user_route(
    user_id: str,
    request: Request,
    payload=Depends(require_role(["admin"]))
):
    success = delete_user_by_id(user_id)

    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint=f"/admin/users/{user_id}",
        method="DELETE",
        status=200 if success else 404,
        ip=getattr(request.state, "ip", None) or (request.client.host if request.client else None),
        user_agent=getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
    )

    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"message": "🗑️ Usuario eliminado correctamente"}

# 🔹 3. Exportar usuarios a CSV (solo admin)
@router.get(
    "/admin/users/export",
    summary="Exportar usuarios a CSV",
    response_class=StreamingResponse,
)
@limit("10/minute")  # exportaciones son costosas
def exportar_usuarios_csv_route(
    request: Request,
    payload=Depends(require_role(["admin"]))
):
    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint="/admin/users/export",
        method="GET",
        status=200,
        ip=getattr(request.state, "ip", None) or (request.client.host if request.client else None),
        user_agent=getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
    )

    return export_users_csv()

# 🔐 4. Crear usuario desde el panel (solo admin)
@router.post(
    "/admin/create-user",
    summary="Crear nuevo usuario",
    response_model=UserOut,
)
@limit("10/minute")  # creación/actualización con límite conservador
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
            ip=getattr(request.state, "ip", None) or (request.client.host if request.client else None),
            user_agent=getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
        )

        return UserOut(
            id=nuevo_usuario["_id"],
            email=nuevo_usuario["email"],
            nombre=user.nombre,
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
            ip=getattr(request.state, "ip", None) or (request.client.host if request.client else None),
            user_agent=getattr(request.state, "user_agent", None) or request.headers.get("user-agent"),
        )
        raise HTTPException(status_code=400, detail=str(e))
