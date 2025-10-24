import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ====================================
# 🔐 AUTENTICACIÓN PARA TESTS
# ====================================

ADMIN_TOKEN = os.getenv("ADMIN_TEST_TOKEN", "Bearer TESTTOKEN_ADMIN")
HEADERS = {"Authorization": ADMIN_TOKEN}

@pytest.fixture
def admin_headers():
    return {"Authorization": ADMIN_TOKEN}

# ====================================
# 📄 CRUD DE INTENTS
# ====================================

def test_create_intent(admin_headers):
    intent_data = {
        "intent": "saludo.test",
        "examples": ["Hola", "Buenos días"],
        "responses": ["¡Hola! ¿Cómo estás?"]
    }
    res = client.post("/admin/intents", json=intent_data, headers=admin_headers)
    assert res.status_code in (200, 400)
    if res.status_code == 200:
        assert "Intent agregado" in res.json()["message"]
    elif res.status_code == 400:
        assert "ya existe" in res.json()["detail"]

def test_list_intents(admin_headers):
    res = client.get("/admin/intents", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_delete_intent(admin_headers):
    res = client.delete("/admin/intents/saludo.test", headers=admin_headers)
    assert res.status_code in (200, 404)

# ====================================
# 📤 EXPORTACIÓN E IMPORTACIÓN
# ====================================

def test_export_intents_csv(admin_headers):
    res = client.get("/admin/intents/export", headers=admin_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    contenido = res.content.decode("utf-8")
    assert "intent" in contenido and "examples" in contenido and "responses" in contenido

def test_upload_intents_csv(admin_headers):
    csv_content = (
        "intent,examples,responses\n"
        "prueba_csv,\"hola\\nbuenas\",\"¡Hola!\\n¿Qué tal?\""
    )
    files = {
        "file": ("intents.csv", csv_content, "text/csv")
    }
    res = client.post("/admin/intents/upload", headers=admin_headers, files=files)
    assert res.status_code == 200
    assert "✅ Intents cargados" in res.json()["message"]

# ====================================
# 🤖 ENTRENAMIENTO DEL BOT
# ====================================

def test_train_bot(admin_headers):
    res = client.post("/admin/train", headers=admin_headers)
    assert res.status_code == 200
    assert "entrenado" in res.json()["message"]

# ====================================
# 📊 ESTADÍSTICAS
# ====================================

def test_stats_admin(admin_headers):
    res = client.get("/admin/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_logs" in data
    assert "intents_distintos" in data
    assert isinstance(data["intents_distintos"], int)
