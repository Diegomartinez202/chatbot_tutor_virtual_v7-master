from __future__ import annotations

from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config.settings import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Intentamos usar primero el jwt_manager (usado en tu proyecto)
_decode_funcs = []
try:
    from backend.utils.jwt_manager import decode_token as _jm_decode  # type: ignore
    _decode_funcs.append(("jwt_manager", _jm_decode))
except Exception:
    pass

# Luego jwt_service (también presente en tu base)
try:
    from backend.services import jwt_service  # type: ignore
    _decode_funcs.append(("jwt_service.decode_token", jwt_service.decode_token))
    # Soporte FAKE token para demo si existe
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
    Middleware de **identificación**:
      - Si DEMO_MODE y token == FAKE_TOKEN_ZAJUNA → asigna claims de demo.
      - Si hay Authorization Bearer real → intenta decodificar con las
        implementaciones disponibles (jwt_manager, luego jwt_service).
      - Nunca bloquea la request; si falla, continúa sin user.
      - La autorización se resuelve en los endpoints con `require_role`.
    """
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(auth_header)

        # DEMO: aceptar token simulado sin romper nada
        if settings.demo_mode and token == FAKE_TOKEN:
            request.state.user = FAKE_CLAIMS
            return await call_next(request)

        # Intentar decodificación real si viene Bearer <token>
        if scheme.lower() == "bearer" and token:
            for name, fn in _decode_funcs:
                try:
                    ok_claims = None
                    # jwt_manager.decode_token(header) → (is_valid, claims) o solo claims según tu versión.
                    result = fn(auth_header) if name == "jwt_service.decode_token" else fn(auth_header)
                    if isinstance(result, tuple) and len(result) == 2:
                        is_valid, claims = result
                        ok_claims = claims if is_valid else None
                    else:
                        # Algunas implementaciones devuelven solo claims o dict
                        ok_claims = result

                    if ok_claims:
                        request.state.user = ok_claims
                        logger.debug(f"[auth] Token válido ({name}). email={ok_claims.get('email')}")
                        break
                except Exception as e:
                    logger.debug(f"[auth] {name} falló: {e}")

        # Si no hubo token o fue inválido, seguimos sin `request.state.user`
        return await call_next(request)