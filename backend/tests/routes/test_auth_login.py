from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_ok(client: TestClient, seed_user):
    payload = {
        "email": seed_user["email"],
        "password": seed_user["password"],
    }
    r = client.post("/api/auth/login", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    # Estructura esperada (no validamos firma ni expiración aquí)
    assert "access_token" in data
    assert "refresh_token" in data
    assert data.get("token_type") == "bearer"


def test_login_fail_bad_password(client: TestClient, seed_user):
    payload = {
        "email": seed_user["email"],
        "password": "mala_clave",
    }
    r = client.post("/api/auth/login", json=payload)
    assert r.status_code in (400, 401), r.text
