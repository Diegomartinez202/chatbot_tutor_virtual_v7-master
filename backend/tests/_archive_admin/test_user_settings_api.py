# tests/test_user_settings_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.mongodb import get_database

client = TestClient(app)

# ⚙️ Datos de ejemplo
FAKE_USER = {"id": "user_demo_001", "email": "demo@example.com"}
HEADERS = {"Authorization": "Bearer FAKE_TOKEN_ZAJUNA"}  # token simulado para demo_mode


@pytest.fixture(autouse=True)
def setup_db():
    """Limpia la colección user_settings antes de cada test."""
    db = get_database()
    db["user_settings"].delete_many({})
    yield


def test_get_user_settings_defaults():
    """Si no existe el usuario → devuelve valores por defecto."""
    resp = client.get("/api/me/settings", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "es"
    assert data["theme"] == "light"
    assert float(data["fontScale"]) == 1.0
    assert data["highContrast"] is False


def test_put_user_settings_and_get_back():
    """PUT guarda correctamente y GET devuelve lo mismo."""
    payload = {
        "language": "en",
        "theme": "dark",
        "fontScale": 1.25,
        "highContrast": True,
    }
    put_resp = client.put("/api/me/settings", json=payload, headers=HEADERS)
    assert put_resp.status_code == 200
    result = put_resp.json()
    assert result["ok"] is True
    prefs = result["prefs"]
    assert prefs["language"] == "en"
    assert prefs["theme"] == "dark"
    assert abs(prefs["fontScale"] - 1.25) < 0.01
    assert prefs["highContrast"] is True

    # Verificar que GET devuelve lo mismo
    get_resp = client.get("/api/me/settings", headers=HEADERS)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["language"] == "en"
    assert data["theme"] == "dark"
    assert abs(data["fontScale"] - 1.25) < 0.01
    assert data["highContrast"] is True
