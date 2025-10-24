import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ⚠️ Reemplaza con un token válido para pruebas locales
TOKEN = os.getenv("TEST_ADMIN_TOKEN", "Bearer TU_TOKEN_AQUI")

HEADERS = {
    "Authorization": TOKEN
}

def test_listar_archivos_log():
    response = client.get("/api/admin/logs", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_descargar_log_invalido():
    response = client.get("/api/admin/logs/hack.txt", headers=HEADERS)
    assert response.status_code == 400

def test_exportar_logs_csv():
    response = client.get("/api/admin/logs/export", headers=HEADERS)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"

def test_contar_mensajes_no_leidos():
    response = client.get("/api/logs/unread_count?user_id=test_user", headers=HEADERS)
    assert response.status_code == 200
    assert "unread" in response.json()

def test_marcar_mensajes_leidos():
    response = client.post("/api/logs/mark_read?user_id=test_user", headers=HEADERS)
    assert response.status_code == 200
    assert "updated_count" in response.json()
