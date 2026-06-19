import requests

BASE_URL = "http://localhost:8000/api"

# ✅ 1. Probar login correcto
def test_login():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@example.com",       # usa el email real de tu admin
        "password": "admin123"
    })

    assert response.status_code == 200, f"Fallo login: {response.text}"
    print("✅ Login exitoso")
    return response.json()["access_token"]

# ✅ 2. Probar acceso a /admin/logs con JWT
def test_logs_protegidos():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/logs", headers=headers)

    assert response.status_code == 200, f"Fallo acceso logs: {response.text}"
    print("✅ Acceso a logs con JWT exitoso")

if __name__ == "__main__":
    test_logs_protegidos()
