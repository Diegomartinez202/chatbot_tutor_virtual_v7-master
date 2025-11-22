
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

client = TestClient(app)

def test_login_fallido():
    res = client.post(
        "/api/auth/login",
        json={"email": "inexistente@test.com", "password": "error123"},
    )
    # según tu implementación puede ser 400 o 401; ajusta si hace falta
    assert res.status_code in (400, 401)
    body = res.json()
    # si tu API devuelve otro detail, ajusta este string
    assert "credenciales" in body.get("detail", "").lower()


def test_me_sin_token():
    res = client.get("/api/auth/me")
    assert res.status_code in (401, 403)


def test_refresh_sin_cookie():
    res = client.post("/api/auth/refresh")
    assert res.status_code in (401, 403)