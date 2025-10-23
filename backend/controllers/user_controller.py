from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from backend.services.user_service import get_users, update_user
from backend.models.user_model import UserUpdate, UserOut
from backend.dependencies.auth import require_role

router = APIRouter()

@router.get("/admin/users", response_model=List[UserOut])
async def listar_usuarios(
    search: str = Query(None),
    skip: int = 0,
    limit: int = 20,
    current_user=Depends(require_role(["admin"]))
):
    return await get_users(search=search, skip=skip, limit=limit)

@router.put("/admin/users/{user_id}", response_model=UserOut)
async def actualizar_usuario(
    user_id: str,
    user_data: UserUpdate,
    current_user=Depends(require_role(["admin"]))
):
    user = await update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user