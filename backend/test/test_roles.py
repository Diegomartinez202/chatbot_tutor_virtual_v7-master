import pytest
from fastapi.testclient import TestClient
from main import app
from backend.dependencies.auth import verify_token, require_role
client = TestClient(app)

admin_token = "Bearer ADMIN_TEST_TOKEN"  # 🔁 reemplaza con un token válido de admin
soporte_token = "Bearer SOPORTE_TEST_TOKEN"
invitado_token = "Bearer INVITADO_TEST_TOKEN"

def test_admin_puede_listar_usuarios():
    res = client.get("/api/admin/users", headers={"Authorization": admin_token})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_invitado_no_puede_listar_usuarios():
    res = client.get("/api/admin/users", headers={"Authorization": invitado_token})
    assert res.status_code == 403  # Forbidden

def test_admin_puede_actualizar_rol_usuario():
    user_id = "ID_DE_USUARIO_A_MODIFICAR"  # 🔁 reemplaza por un _id de prueba
    payload = {
        "nombre": "Usuario de prueba",
        "email": "test@example.com",
        "rol": "soporte"
    }
    res = client.put(f"/api/admin/users/{user_id}", json=payload, headers={"Authorization": admin_token})
    assert res.status_code == 200
    assert res.json()["rol"] == "soporte"

def test_soporte_no_puede_actualizar_roles():
    user_id = "ID_DE_USUARIO_A_MODIFICAR"
    payload = {
        "nombre": "Usuario de prueba",
        "email": "test@example.com",
        "rol": "admin"
    }
    res = client.put(f"/api/admin/users/{user_id}", json=payload, headers={"Authorization": soporte_token})
    assert res.status_code == 403