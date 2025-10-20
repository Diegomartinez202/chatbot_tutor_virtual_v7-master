# tests/test_profile.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

admin_credentials = {
    "email": "admin@example.com",
    "password": "contrasenaSegura123"
}

def get_token():
    response = client.post("/auth/login", json=admin_credentials)
    assert response.status_code == 200
    return response.json()["access_token"]

def test_get_profile():
    token = get_token()
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "email" in res.json()
    assert res.json()["email"] == admin_credentials["email"]

