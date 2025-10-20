# backend/tests/test_functional_flow.py
import requests

BASE_URL = "http://localhost:8000"  # Puedes cambiar por os.getenv() si quieres

admin_user = {"email": "admin@example.com", "password": "123456"}
intent_payload = {
    "intent": "saludo",
    "responses": ["¡Hola! ¿En qué puedo ayudarte?"]
}


def test_register_user():
    res = requests.post(f"{BASE_URL}/api/auth/register", json=admin_user)
    assert res.status_code in [200, 400]  # 400 si ya existe
    print("✅ Registro:", res.status_code)


def test_login_get_token():
    res = requests.post(f"{BASE_URL}/api/auth/login", json=admin_user)
    assert res.status_code == 200
    global token
    token = res.json().get("access_token")
    assert token
    print("🔐 Token recibido")


def test_create_intent():
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post(f"{BASE_URL}/api/admin/intents", json=intent_payload, headers=headers)
    assert res.status_code in [200, 201, 409]  # 409 si ya existe
    print("✅ Intent creado")


def test_retrain_bot():
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post(f"{BASE_URL}/api/admin/retrain", headers=headers)
    assert res.status_code == 200
    print("🔄 Reentrenamiento exitoso")


def test_send_message():
    res = requests.post(f"{BASE_URL}/chat", json={"user_id": "anonimo", "message": "Hola"})
    assert res.status_code == 200
    respuesta = res.json()
    assert isinstance(respuesta, list)
    print("🤖 Respuesta recibida:", respuesta)


def test_logs_access():
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/api/logs", headers=headers)
    assert res.status_code == 200
    print("📄 Logs disponibles:", len(res.json()))
