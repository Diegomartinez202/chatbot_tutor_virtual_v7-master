# backend/test/routes/test_profile_me.py
from __future__ import annotations

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_get_profile_me():
    """
    Flujo:
      1) Registrar o asegurar usuario
      2) Login en /api/auth/login
      3) GET /api/auth/me con el token
    """
    email = "profile_test@example.com"
    password = "profile123"
    rol = "admin"

    # 1) Registrar usuario (idempotente: 200 o 400 si ya existe)
    r_reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "rol": rol},
    )
    assert r_reg.status_code in (200, 400), r_reg.text

    # 2) Login
    r_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert r_login.status_code == 200, r_login.text
    tokens = r_login.json()
    access = tokens["access_token"]

    # 3) /api/auth/me
    r_me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r_me.status_code == 200, r_me.text
    data = r_me.json()
    assert data["email"] == email
    assert data["rol"] == rol
