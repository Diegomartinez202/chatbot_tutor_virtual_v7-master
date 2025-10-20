from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)
TOKEN = os.getenv("ADMIN_TEST_TOKEN", "Bearer TESTTOKEN")
headers = {"Authorization": TOKEN}

def test_entrenamiento_manual():
    res = client.post("/api/admin/train", headers=headers)
    assert res.status_code == 200
    assert "log_file" in res.json()