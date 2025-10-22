# backend/services/jwt_service.py
from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import jwt
from jwt import InvalidTokenError, PyJWKClient

from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# === 🔧 MODO DEMO AUTENTICACIÓN (FAKE TOKEN ZAJUNA) ===
# Permite simular un token válido para la sustentación sin conexión al sistema real.
FAKE_DEMO_TOKEN = "FAKE_TOKEN_ZAJUNA"
FAKE_DEMO_CLAIMS = {
    "sub": "demo_user_zajuna",
    "name": "Usuario de Prueba Zajuna",
    "email": "demo@zajuna.edu.co",
    "role": "student",
    "iss": "zajuna.demo",
    "iat": 1730000000,
    "exp": 1750000000,
}


# ============================================================
# 🔑 FUNCIÓN PRINCIPAL DE DECODIFICACIÓN DE TOKEN
# ============================================================
def decode_token(auth_header: Optional[str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Versión extendida: incluye soporte para token simulado de Zajuna en modo DEMO.
    """
    token = get_bearer_token(auth_header)
    if not token:
        return False, {}

    # 🧩 Simular autenticación Zajuna en modo demo
    if settings.demo_mode and token == FAKE_DEMO_TOKEN:
        logger.warning("[Auth] Modo DEMO activo: aceptando token simulado Zajuna")
        return True, FAKE_DEMO_CLAIMS

    # Si no es el token demo, continuar con la verificación normal
    return decode_raw_token(token)


# ============================================================
# 🔍 UTILIDADES JWT
# ============================================================
def get_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Extrae el token Bearer de un header Authorization.
    """
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _jwt_decode_options() -> Dict[str, Any]:
    """
    Opciones de verificación ajustables vía settings.
    """
    return {
        "require": [],  # puedes exigir ["exp", "iat"] si lo deseas
    }


def _jwt_decode_kwargs() -> Dict[str, Any]:
    """
    Construye kwargs para jwt.decode en base a settings.
    """
    kwargs: Dict[str, Any] = {
        "algorithms": [settings.jwt_algorithm.upper()],
        "options": _jwt_decode_options(),
    }

    # issuer (opcional)
    iss = getattr(settings, "jwt_issuer", None)
    if iss:
        kwargs["issuer"] = iss

    # audience (opcional)
    aud = getattr(settings, "jwt_audience", None)
    if aud:
        kwargs["audience"] = aud

    # leeway (opcional, segundos)
    leeway = getattr(settings, "leeway_seconds", None)
    if isinstance(leeway, int) and leeway > 0:
        kwargs["leeway"] = leeway

    return kwargs


# ============================================================
# 🔐 DECODIFICACIÓN SEGURA DE JWT
# ============================================================
def decode_raw_token(token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Decodifica/verifica un JWT crudo (sin 'Bearer ') usando HS* o RS*/JWKS.
    Devuelve (ok, claims).
    """
    alg = settings.jwt_algorithm.upper()
    kwargs = _jwt_decode_kwargs()

    try:
        # HS* (clave simétrica)
        if alg.startswith("HS"):
            secret = getattr(settings, "secret_key", None)
            if not secret:
                return False, {}
            claims = jwt.decode(token, secret, **kwargs)
            return True, claims

        # RS* (llave pública PEM o JWKS)
        if alg.startswith("RS"):
            # 1) JWKS si se configuró
            jwks_url = getattr(settings, "jwt_jwks_url", None)
            if jwks_url:
                try:
                    jwk_client = PyJWKClient(jwks_url)
                    signing_key = jwk_client.get_signing_key_from_jwt(token)
                    claims = jwt.decode(token, signing_key.key, **kwargs)
                    return True, claims
                except Exception:
                    # Si JWKS falla, intentamos con clave pública local si existe
                    pass

            # 2) Clave pública local (PEM)
            pub_key = getattr(settings, "jwt_public_key", None)
            if not pub_key:
                return False, {}
            claims = jwt.decode(token, pub_key, **kwargs)
            return True, claims

        # Algoritmo no soportado
        return False, {}

    except InvalidTokenError:
        return False, {}
    except Exception:
        # Cualquier otro error: no exponemos detalles por seguridad
        return False, {}


# ============================================================
# 📜 VERIFICACIÓN SIMPLE
# ============================================================
def verify_token(token: str) -> Dict[str, Any]:
    """
    Igual que decode_raw_token, pero retorna solo claims (o {} si inválido).
    Útil si el caller sólo necesita los claims.
    """
    ok, claims = decode_raw_token(token)
    return claims if ok else {}


# ============================================================
# 🔁 FUNCIÓN COMPATIBLE CON LEGACY CODE
# ============================================================
def decode_token_legacy(auth_header: Optional[str]) -> Tuple[bool, Dict[str, Any]]:
    """
    API LEGADA (se mantiene la firma para no romper dependientes):
    Recibe el header Authorization y retorna (ok, claims).
    """
    token = get_bearer_token(auth_header)
    if not token:
        return False, {}
    return decode_raw_token(token)


__all__ = [
    "get_bearer_token",
    "decode_raw_token",
    "verify_token",
    "decode_token",
    "decode_token_legacy",
]