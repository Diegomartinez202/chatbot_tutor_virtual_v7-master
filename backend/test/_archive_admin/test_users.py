import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ============================
# 🔐 CREDENCIALES Y DATOS
# ============================

admin_credentials = {
    "email": "admin@example.com",
    "password": "contrasenaSegura123"
}

test_user = {
    "nombre": "Usuario Test",
    "email": "usertest@example.com",
    "rol": "soporte",
    "password": "testpassword123"
}

updated_user = {
    "nombre": "Usuario Actualizado",
    "email": "usertest@example.com",
    "rol": "admin"
}


# ============================
# 🔐 FUNCIONES AUXILIARES
# ============================

def get_token():
    response = client.post("/api/auth/login", json=admin_credentials)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_user_id(headers):
    response = client.get("/api/admin/users", headers=headers)
    users = response.json()
    user = next((u for u in users if u["email"] == test_user["email"]), None)
    return user["id"] if user else None


# ============================
# ✅ TESTS CRUD DE USUARIOS
# ============================

def test_create_user():
    headers = get_token()
    response = client.post("/api/admin/users", json=test_user, headers=headers)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        assert "id" in response.json()
    elif response.status_code == 400:
        assert "ya existe" in response.json()["detail"]

def test_list_users():
    headers = get_token()
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert any(u["email"] == test_user["email"] for u in users)

def test_update_user():
    headers = get_token()
    user_id = get_user_id(headers)
    assert user_id is not None, "El usuario de prueba no existe"

    response = client.put(f"/api/admin/users/{user_id}", json=updated_user, headers=headers)
    assert response.status_code == 200
    assert "actualizado" in response.json()["message"]

def test_delete_user():
    headers = get_token()
    user_id = get_user_id(headers)
    assert user_id is not None, "El usuario de prueba no existe"

    response = client.delete(f"/api/admin/users/{user_id}", headers=headers)
    assert response.status_code == 200
    assert "eliminado" in response.json()["message"]
def test_export_users_csv():
    headers = get_token()
    response = client.get("/api/admin/users/export", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=usuarios_exportados.csv" in response.headers["content-disposition"]

    # Validar contenido mínimo del CSV
    contenido = response.content.decode("utf-8")
    assert "nombre,email,rol" in contenido  # encabezado CSV
