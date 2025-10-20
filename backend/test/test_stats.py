import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ============================
# 🔐 TOKENS DE PRUEBA
# ============================

@pytest.fixture
def soporte_headers():
    return {"Authorization": "Bearer TESTTOKEN_SOPORTE"}

@pytest.fixture
def jwt_headers():
    return {"Authorization": "Bearer TOKEN_VALIDO_JWT"}

# ============================
# 🔎 PRUEBA: /admin/stats
# ============================

def test_get_admin_stats(soporte_headers):
    response = client.get("/admin/stats", headers=soporte_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_logs" in data
    assert "intents_distintos" in data
    assert isinstance(data["total_logs"], int)
    assert isinstance(data["intents_distintos"], int)

# ============================
# 📊 PRUEBA: /api/stats (dashboard)
# ============================

def test_get_dashboard_stats(jwt_headers):
    response = client.get("/api/stats", headers=jwt_headers)
    assert response.status_code == 200
    data = response.json()

    assert "total_conversaciones" in data
    assert "intents_mas_usados" in data
    assert "usuarios_por_rol" in data
    assert "actividad_por_dia" in data

    assert isinstance(data["intents_mas_usados"], list)
    assert isinstance(data["usuarios_por_rol"], list)
    assert isinstance(data["actividad_por_dia"], list)
