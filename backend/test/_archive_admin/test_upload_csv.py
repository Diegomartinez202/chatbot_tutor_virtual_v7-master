import pytest
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

@pytest.fixture
def admin_headers():
    return {"Authorization": "Bearer TESTTOKEN_ADMIN"}

def test_upload_intents_csv(admin_headers):
    # Crear contenido CSV simulado
    csv_content = (
        "intent,examples,responses\n"
        "saludo,hola\\nhola bot\\nqué tal?,Hola!\\nQué puedo hacer por ti?"
    )
    files = {
        "file": ("intents.csv", csv_content, "text/csv")
    }

    response = client.post("/admin/intents/upload", headers=admin_headers, files=files)
    assert response.status_code == 200
    assert "message" in response.json()
