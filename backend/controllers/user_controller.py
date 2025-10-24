# =====================================================
# 🧩 backend/controllers/user_controller.py
# =====================================================
from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr

from backend.dependencies.auth import require_role
from backend.schemas.user_schema import UserOut
from backend.services.user_service import list_users, update_user as update_user_service

router = APIRouter(prefix="/api/admin", tags=["Admin Users"])


# Modelo de actualización local (ligero y compatible con user_service.update_user)
class UserUpdateIn(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    password: Optional[str] = None


@router.get("/users", response_model=List[UserOut])
def listar_usuarios(
    search: Optional[str] = Query(None, description="Filtrar por nombre/email (contiene)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    current_user=Depends(require_role(["admin"]))
):
    """
    Lista usuarios con filtro opcional y paginación simple.
    Usa list_users() y filtra en memoria para no romper servicios existentes.
    """
    users = list_users()  # ya excluye password

    # Filtrado ligero en memoria (nombre/email contiene 'search')
    if search:
        s = search.strip().lower()
        users = [
            u for u in users
            if (u.nombre or "").lower().__contains__(s) or (u.email or "").lower().__contains__(s)
        ]

    # Paginación simple en memoria
    start = max(0, int(skip))
    end = start + int(limit)
    return users[start:end]


@router.put("/users/{user_id}", response_model=UserOut)
def actualizar_usuario(
    user_id: str,
    user_data: UserUpdateIn = Body(...),
    current_user=Depends(require_role(["admin"]))
):
    """
    Actualiza campos básicos del usuario.
    Delegamos en user_service.update_user(user_id, data_dict) que ya:
    - valida ObjectId
    - hashea password si viene
    - evita duplicar email
    """
    payload: Dict[str, Any] = user_data.model_dump(exclude_unset=True)
    updated = update_user_service(user_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no actualizado")

    # Normalizar salida a UserOut
    return UserOut(
        id=str(updated.get("_id", "")),
        email=updated.get("email", ""),
        nombre=updated.get("nombre", ""),
        rol=updated.get("rol", "usuario"),
    )