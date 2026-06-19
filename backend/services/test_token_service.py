# tests/services/test_token_service.py
from __future__ import annotations

import time
import jwt
import pytest

from backend.services import token_service
from backend.config import settings as settings_mod


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    # HS256 + SECRET_KEY para emisión/validación
    monkeypatch.setattr(settings_mod.settings, "jwt_algorithm", "HS256", raising=False)
    monkeypatch.setattr(settings_mod.settings, "secret_key", "TEST_SECRET_KEY", raising=False)
    monkeypatch.setattr(settings_mod.settings, "access_token_expire_minutes", 1, raising=False)
    # permitir tokens sin typ en tests específicos
    monkeypatch.setattr(settings_mod.settings, "jwt_accept_typeless", True, raising=False)
    yield


def test_create_and_decode_access_token_ok():
    payload = {"sub": "user123", "email": "user@test.com", "role": "user"}
    tok = token_service.create_access_token(payload)
    assert isinstance(tok, str) and len(tok) > 10

    dec = token_service.decode_access_token(tok)
    assert dec is not None
    assert dec["sub"] == "user123"
    assert dec["email"] == "user@test.com"
    assert dec["role"] == "user"
    assert dec["typ"] == "access"


def test_create_and_decode_refresh_token_ok():
    payload = {"sub": "user123"}
    tok = token_service.create_refresh_token(payload)
    dec = token_service.decode_refresh_token(tok)
    assert dec is not None
    assert dec["sub"] == "user123"
    assert dec["typ"] == "refresh"


def test_decode_access_wrong_typ_returns_none():
    # Generamos un token con typ=refresh y lo intentamos validar como access
    payload = {"sub": "abc"}
    refresh = token_service.create_refresh_token(payload)
    assert token_service.decode_access_token(refresh) is None


def test_typeless_token_with_flag_allows_decode(monkeypatch):
    # Token sin 'typ': lo decodificamos aceptándolo por compatibilidad
    payload = {"sub": "no-typ"}
    tok = jwt.encode(payload, settings_mod.settings.secret_key, algorithm=settings_mod.settings.jwt_algorithm)

    # Caso 1: allow_typeless=True explícito
    dec1 = token_service.decode_access_token(tok, allow_typeless=True)
    assert dec1 is not None
    assert dec1["sub"] == "no-typ"

    # Caso 2: usando settings.jwt_accept_typeless=True (ya parcheado en fixture)
    dec2 = token_service.decode_access_token(tok)
    assert dec2 is not None


def test_reissue_from_refresh_ok():
    payload = {"sub": "reissue-user", "scope": "all"}
    refresh = token_service.create_refresh_token(payload)

    pair = token_service.reissue_tokens_from_refresh(refresh)
    assert pair is not None
    access2, refresh2 = pair
    assert isinstance(access2, str) and isinstance(refresh2, str)
    dec_access2 = token_service.decode_access_token(access2)
    dec_refresh2 = token_service.decode_refresh_token(refresh2)
    assert dec_access2 is not None and dec_refresh2 is not None
    assert dec_access2["sub"] == "reissue-user"
    assert dec_access2["scope"] == "all"


def test_expired_access_token_returns_none(monkeypatch):
    # Forzamos un access token a expirar casi de inmediato
    monkeypatch.setattr(settings_mod.settings, "access_token_expire_minutes", 0, raising=False)
    tok = token_service.create_access_token({"sub": "will-expire"})
    time.sleep(1)  # deja expirar
    assert token_service.decode_access_token(tok) is None