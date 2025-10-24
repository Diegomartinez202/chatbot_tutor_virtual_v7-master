# backend/routes/demo_routes.py
from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict
from backend.config.settings import settings

router = APIRouter(tags=["Demo / FAKE_TOKEN_ZAJUNA"])

FAKE_TOKEN = "FAKE_TOKEN_ZAJUNA"

def demo_auth(request: Request) -> Dict:
    """
    Valida token demo sin tocar JWT real.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ", 1)[1]
    if settings.demo_mode and token == FAKE_TOKEN:
        # Claims de prueba
        return {
            "sub": "demo_user",
            "rol": "demo",
            "email": "demo@zajuna.com",
            "name": "Demo User",
        }
    raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
def demo_me(claims: Dict = Depends(demo_auth)):
    """
    Endpoint demo: retorna info simulada del usuario logueado con FAKE_TOKEN_ZAJUNA
    """
    return {"ok": True, "user": claims}