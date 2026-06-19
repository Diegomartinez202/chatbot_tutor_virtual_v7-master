# backend/auth/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from backend.dependencies.auth import verify_token

# Middleware/extractor de tokens obligatorio
security = HTTPBearer()

# Versión opcional: NO obliga a enviar token (útil para chatbot invitado)
security_optional = HTTPBearer(auto_error=False)


# Modelo del usuario autenticado
class CurrentUser(BaseModel):
    id: str
    email: str


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Obtiene el usuario ACTUAL usando el mismo JWT que valida todo el backend.
    - Si el token es válido → devuelve CurrentUser con id y email.
    - Si el token es inválido/expirado → verify_token lanzará 401 automáticamente.
    """
    token = creds.credentials

    # Reutilizamos la lógica central de JWT (backend/dependencies/auth.verify_token)
    user_data = verify_token(token)  # {'id': ..., 'email': ..., 'rol': ...}

    return CurrentUser(
        id=user_data["id"],
        email=user_data.get("email") or "",
    )


def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[CurrentUser]:
    """
    Devuelve:
    - CurrentUser si hay token válido.
    - None si NO hay token o si es inválido.

    Ideal para /api/chat:
    - Permite modo invitado (sin Authorization).
    - También soporta estudiantes/admin cuando el front/envíe un token válido.
    """
    # No se envió Authorization → invitado
    if creds is None:
        return None

    token = creds.credentials

    try:
        user_data = verify_token(token)
        return CurrentUser(
            id=user_data["id"],
            email=user_data.get("email") or "",
        )
    except HTTPException:
        # Token inválido/expirado → lo tratamos como invitado
        return None

