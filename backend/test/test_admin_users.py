import pytest
from fastapi.testclient import TestClient
from main import app
from backend.utils.jwt_manager import create_access_token

client = TestClient(app)

admin_email = "admin@example.com"
admin_rol = "admin"
admin_token = create_access_token({"sub": admin_email, "rol": admin_rol})

headers_admin = {"Authorization": f"Bearer {admin_token}"}

# === LISTAR USUARIOS ===

def test_list_users():
    res = client.get("/api/admin/users", headers=headers_admin)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert "email" in res.json()[0]

# === ACTUALIZAR USUARIO ===

def test_update_user():
    # 1. Obtener usuario existente
    res = client.get("/api/admin/users", headers=headers_admin)
    user = res.json()[0]
    user_id = user["id"]

    # 2. Actualizar el nombre o rol del usuario
    update_data = {"nombre": "Nombre Actualizado", "rol": "soporte"}
    res_update = client.put(f"/api/admin/users/{user_id}", json=update_data, headers=headers_admin)
    assert res_update.status_code == 200
    assert res_update.json()["rol"] == "soporte"

# === ELIMINAR USUARIO (opcional en pruebas reales) ===

def test_delete_user_temporal():
    # ⚠️ Solo eliminar usuarios creados específicamente para test
    # Crear nuevo usuario para eliminarlo luego
    email = "delete_me@example.com"
    password = "test123"
    rol = "usuario"

    res_create = client.post("/api/auth/register", json={"email": email, "password": password, "rol": rol})
    assert res_create.status_code in [200, 400]  # Puede fallar si ya existe

    # Buscar ese usuario
    res = client.get("/api/admin/users", headers=headers_admin)
    user = next((u for u in res.json() if u["email"] == email), None)
    assert user is not None

    # Eliminarlo
    res_delete = client.delete(f"/api/admin/users/{user['id']}", headers=headers_admin)
    assert res_delete.status_code == 200
    assert res_delete.json()["message"] == "Usuario eliminado correctamente"