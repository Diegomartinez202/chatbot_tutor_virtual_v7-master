from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_test_history():
    res = client.get("/api/admin/test-history", headers={"Authorization": "Bearer TESTTOKEN"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_train_endpoint():
    res = client.post("/api/admin/train", headers={"Authorization": "Bearer TESTTOKEN"})
    assert res.status_code == 200
    assert "returncode" in res.json()
