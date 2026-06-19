# backend/middleware/auth_middleware.py
from __future__ import annotations

from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config.settings import settings
from backend.utils.logging import get_logger

# 👇 Importamos el enum de roles (no rompe nada, solo nos da valores válidos)
from backend.models.user_model import RolEnum

logger = get_logger(__name__)

# Probamos primero jwt_manager
_decode_funcs = []
try:
    from backend.utils.jwt_manager import decode_token as _jm_decode  # type: ignore
    _decode_funcs.append(("jwt_manager.decode_token", _jm_decode))
except Exception:
    pass

# Luego jwt_service (si existe)
try:
    from backend.services import jwt_service  # type: ignore
    _decode_funcs.append(("jwt_service.decode_token", getattr(jwt_service, "decode_token")))
    FAKE_TOKEN = getattr(jwt_service, "FAKE_DEMO_TOKEN", "FAKE_TOKEN_ZAJUNA")
    FAKE_CLAIMS = getattr(jwt_service, "FAKE_DEMO_CLAIMS", {
        "sub": "demo_user",
        "rol": "demo",
        "email": "demo@zajuna.com",
        "name": "Demo User",
    })
except Exception:
    jwt_service = None  # type: ignore
    FAKE_TOKEN = "FAKE_TOKEN_ZAJUNA"
    FAKE_CLAIMS = {
        "sub": "demo_user",
        "rol": "demo",
        "email": "demo@zajuna.com",
        "name": "Demo User",
    }


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware de identificación:
      - Si DEMO_MODE y token == FAKE_TOKEN_ZAJUNA → asigna claims de demo.
      - Si hay Authorization Bearer → intenta decodificar con jwt_manager / jwt_service.
      - Nunca bloquea: autorización se hace en endpoints con require_role/Depends.
    """
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization", "")
        scheme, token = get_authorization_scheme_param(auth_header)

        # DEMO
        if settings.demo_mode and token == FAKE_TOKEN:
            # 👇 normalizamos también el rol en modo demo, por si lo quieres usar
            claims = dict(FAKE_CLAIMS)
            raw_role = claims.get("rol") or "usuario"
            try:
                normalized_role = RolEnum(raw_role).value
            except ValueError:
                normalized_role = RolEnum.usuario.value
            claims["rol"] = normalized_role
            request.state.user = claims
            return await call_next(request)

        # Bearer real
        if (scheme or "").lower() == "bearer" and token:
            for name, fn in _decode_funcs:
                try:
                    # tus funciones suelen aceptar el header completo
                    result = fn(auth_header)
                    claims = None

                    if isinstance(result, tuple) and len(result) == 2:
                        is_valid, payload = result
                        claims = payload if is_valid else None
                    else:
                        # algunas devuelven directamente el dict
                        claims = result

                    if isinstance(claims, dict) and claims:
                        # 👇 AQUÍ ES DONDE AÑADIMOS LA MEJORA
                        #   - Respetar "rol" si viene como estudiante, admin, soporte, usuario, etc.
                        #   - Si viene algo raro, forzamos "usuario" (seguro).
                        raw_role = (
                            claims.get("rol")
                            or claims.get("role")
                            or claims.get("scope")
                            or "usuario"
                        )
                        try:
                            normalized_role = RolEnum(raw_role).value
                        except ValueError:
                            normalized_role = RolEnum.usuario.value

                        claims["rol"] = normalized_role

                        request.state.user = claims
                        logger.debug(f"[auth] Token válido por {name} ({claims.get('email')})")
                        break
                except Exception as e:
                    logger.debug(f"[auth] {name} falló: {e}")

        return await call_next(request)
