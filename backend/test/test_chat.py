# tests/test_chat.py
import jwt
import pytest
import respx
import httpx

from fastapi.testclient import TestClient

from backend.main import app
from backend.config.settings import settings

client = TestClient(app)

@pytest.fixture
def rasa_mock():
    """Mock de la URL de Rasa."""
    with respx.mock(assert_all_called=True) as respx_mock:
        yield respx_mock

def _build_token(claims: dict) -> str:
    """Construye un JWT HS* para pruebas locales."""
    key = settings.secret_key or "test_secret_key_12345678901234567890"
    alg = (settings.jwt_algorithm or "HS256").upper()
    return jwt.encode(claims, key, algorithm=alg)

def _assert_forwarded_auth(respx_call, expected_has_token: bool):
    """Valida que metadata.auth.hasToken coincide con lo esperado."""
    sent_json = respx_call.request.json()
    meta = (sent_json or {}).get("metadata", {})
    auth = meta.get("auth", {})
    assert auth.get("hasToken") is expected_has_token

def _assert_request_id_header(respx_call):
    """Valida que X-Request-ID fue propagado a Rasa."""
    assert "X-Request-ID" in respx_call.request.headers
    assert len(respx_call.request.headers["X-Request-ID"]) > 0


@pytest.mark.parametrize("endpoint", ["/chat", "/api/chat"])
def test_without_token(endpoint, rasa_mock):
    """Prueba ambos endpoints sin token."""
    mock_call = rasa_mock.post(settings.rasa_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json=[{"recipient_id": "anonimo", "text": "Necesitas iniciar sesión."}],
        )
    )

    payload = {"sender": "anonimo", "message": "/ver_certificados", "metadata": {}}
    res = client.post(endpoint, json=payload)

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

    assert mock_call.called
    _assert_forwarded_auth(mock_call.calls.last, expected_has_token=False)
    _assert_request_id_header(mock_call.calls.last)


@pytest.mark.parametrize("endpoint", ["/chat", "/api/chat"])
def test_with_token(endpoint, rasa_mock):
    """Prueba ambos endpoints con token válido."""
    token = _build_token({"sub": "user123", "role": "student"})
    mock_call = rasa_mock.post(settings.rasa_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json=[{"recipient_id": "user123", "text": "Lista de certificados..."}],
        )
    )

    payload = {"sender": "user123", "message": "/ver_certificados", "metadata": {}}
    res = client.post(endpoint, json=payload, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

    assert mock_call.called
    _assert_forwarded_auth(mock_call.calls.last, expected_has_token=True)
    _assert_request_id_header(mock_call.calls.last)