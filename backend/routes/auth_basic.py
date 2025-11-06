from __future__ import annotations
from fastapi import APIRouter, Depends
from backend.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.get("/me")
def auth_me(user=Depends(get_current_user)):
    # Normalización simple para el panel
    return {"id": user.get("id"), "email": user.get("email"), "rol": user.get("rol")}

@router.post("/logout")
def auth_logout():
    # Si luego manejas cookies httpOnly, aquí las limpiarías.
    return {"ok": True}
