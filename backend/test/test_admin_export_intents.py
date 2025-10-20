import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 🔐 Reemplaza este token con uno válido si JWT está activo
HEADERS = {"Authorization": "Bearer TESTTOKEN123"}

def test_exportar_intents_csv(monkeypatch):
    # 👉 Simular datos desde MongoDB
    def mock_get_intents_collection():
        return [
            {
                "intent": "saludo",
                "examples": ["hola", "buenos días"],
                "response": "¡Hola! ¿En qué puedo ayudarte?"
            }
        ]

    from backend.routes import admin
    monkeypatch.setattr(admin, "get_intents_collection", lambda: DummyCursor(mock_get_intents_collection()))

    response = client.get("/api/admin/intents/export", headers=HEADERS)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "intent" in response.text.lower()

# 👇 Dummy que imita el cursor de Mongo async
class DummyCursor:
    def __init__(self, data):
        self._data = data

    async def to_list(self, length=None):
        return self._data()