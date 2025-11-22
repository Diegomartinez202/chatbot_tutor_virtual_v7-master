# backend/test_adapted/unit/test_unit_jwt_manager.py
import jwt
from datetime import timedelta, datetime, timezone

from backend.utils.jwt_manager import create_access_token
from backend.config.settings import settings


def test_create_access_token_roundtrip():
    """
    Verifica que create_access_token genere un JWT válido
    y que se pueda decodificar con la SECRET_KEY y algoritmo del proyecto.
    """
    payload = {"sub": "user@example.com", "rol": "admin"}
    token = create_access_token(payload, expires_minutes=30)

    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # header.payload.signature

    decoded = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert decoded.get("sub") == "user@example.com"
    assert decoded.get("rol") == "admin"
    # Debe haber un claim de expiración
    assert "exp" in decoded


def test_create_access_token_explicit_exp():
    """
    Opcional: si create_access_token acepta un delta, validamos que respete la expiración.
    Si tu firma es distinta, ajusta este test.
    """
    payload = {"sub": "demo@test.com"}
    # Forzamos exp corto
    token = create_access_token(payload, expires_minutes=1)
    decoded = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    exp_ts = decoded["exp"]
    exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    assert (exp_dt - now) <= timedelta(minutes=2)
