# backend/test_adapted/functional/test_func_auth_guards.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_login_con_credenciales_invalidas():
    """
    Escenario: intento de login con usuario que no existe.

    No depende de usuarios reales del SENA ni de Zajuna.
    """
    r = client.post(
        "/api/auth/login",
        json={"email": "inexistente@test.com", "password": "clave_invalida"},
    )

    # Algunos backends usan 400, otros 401, otros 422 (validación de schema)
    assert r.status_code in (400, 401, 422), r.text

    data = r.json()
    # No imponemos un mensaje exacto, solo que haya un detalle de error
    assert "detail" in data


def test_me_requiere_token():
    """
    /api/auth/me debe estar protegido:
      - sin token → 401/403 (no autenticado / no autorizado)
    """
    r = client.get("/api/auth/me")
    assert r.status_code in (401, 403)


def test_refresh_sin_cookie_refresh_token():
    """
    /api/auth/refresh sin cookie de refresh_token debe ser rechazado.
    No depende de flujos reales de Zajuna.
    """
    r = client.post("/api/auth/refresh")
    assert r.status_code in (401, 400)
