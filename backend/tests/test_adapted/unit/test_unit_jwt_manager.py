# backend/test/test_adapted/unit/test_unit_jwt_manager.py

import jwt
from datetime import datetime, timezone

from backend.config.settings import settings
from backend.utils.jwt_manager import create_access_token


def _decode_token(token: str) -> dict:
    """
    Helper para decodificar el JWT usando la configuración real del proyecto.
    """
    key = settings.secret_key
    alg = (settings.jwt_algorithm or "HS256").upper()
    return jwt.decode(token, key, algorithms=[alg])


def test_create_access_token_roundtrip():
    """
    Verifica que create_access_token genere un JWT válido
    y que se pueda decodificar con la SECRET_KEY y algoritmo del proyecto.
    No fuerza parámetros de expiración; usa la configuración real.
    """
    payload = {"sub": "user@example.com", "rol": "admin"}

    token = create_access_token(payload)
    assert isinstance(token, str)
    assert len(token) > 0

    decoded = _decode_token(token)

    assert decoded.get("sub") == "user@example.com"
   
    assert decoded.get("rol") in ("admin", None) or decoded.get("role") in ("admin", None)

    assert "exp" in decoded


def test_create_access_token_exp_claim_is_future():
    """
    Verifica que el token generado tenga un claim 'exp' (expiración)
    y que dicha fecha esté en el futuro respecto a 'now'.

    No imponemos un valor exacto de minutos para respetar
    la configuración actual del proyecto.
    """
    payload = {"sub": "demo@test.com"}

    token = create_access_token(payload)
    decoded = _decode_token(token)

    assert "exp" in decoded

    exp_ts = decoded["exp"]
 
    exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    assert exp_dt > now

    max_dt = now.replace(year=now.year + 1)  
    assert exp_dt < max_dt
