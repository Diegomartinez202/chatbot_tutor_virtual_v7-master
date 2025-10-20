from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

usuarios = {
    "admin": {"email": "admin@test.com", "password": "admin123"},
    "soporte": {"email": "soporte@test.com", "password": "soporte123"},
    "usuario": {"email": "usuario@test.com", "password": "usuario123"},
}

for rol, creds in usuarios.items():
    res = client.post("/api/auth/login", json=creds)
    token = res.json().get("access_token")
    print(f"{rol.upper()} TOKEN:\nBearer {token}\n")