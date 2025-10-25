# backend/app/auth/deps.py
import os, jwt
from fastapi import HTTPException, status, Request

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

def get_current_user(request: Request):
    # 1) Authorization: Bearer <token>
    auth = request.headers.get("Authorization", "")
    token = None
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    # 2) Cookie (si autenticás por cookie)
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "rol": payload.get("role") or payload.get("rol") or "usuario",
    }
