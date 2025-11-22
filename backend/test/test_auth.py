import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.jwt_manager import create_access_token  # ✅ Necesario
from backend.dependencies.auth import verify_token, require_role
client = TestClient(app)

# 🔐 Datos de prueba
test_email = "testuser@example.com"
test_password = "test1234"
test_rol = "admin"

access_token = None
refresh_token = None

@pytest.fixture(scope="module")
def register_user():
    res = client.post("/api/auth/register", json={
        "email": test_email,
        "password": test_password,
        "rol": test_rol
    })
    assert res.status_code in [200, 400]
    return True

def test_login(register_user):
    global access_token, refresh_token

    res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert res.status_code == 200
    data = res.json()

    access_token = data["access_token"]
    refresh_token = res.cookies.get("refresh_token")

    assert "access_token" in data
    assert data["user"]["email"] == test_email
    assert refresh_token is not None

def test_me():
    assert access_token is not None
    res = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == test_email
    assert data["rol"] == test_rol

def test_refresh_token():
    assert refresh_token is not None
    res = client.post("/api/auth/refresh", cookies={
        "refresh_token": refresh_token
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_logout():
    assert refresh_token is not None
    res = client.post("/api/auth/logout", cookies={
        "refresh_token": refresh_token
    })
    assert res.status_code == 200
    assert res.json()["message"] == "Sesión cerrada correctamente"

# ✅ Nueva mejora: prueba aislada generando token manualmente
def test_refresh_token_direct_cookie():
    fake_token = create_access_token({"sub": "admin@example.com", "rol": "admin"}, expires_minutes=60)
    res = client.post("/api/auth/refresh", cookies={"refresh_token": fake_token})
    assert res.status_code == 200
    assert "access_token" in res.json()
