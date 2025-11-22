# backend/test_adapted/functional/test_func_chat_auth_sensitive.py
import pytest
import httpx
import respx
from fastapi.testclient import TestClient

from backend.main import app
from backend.config.settings import settings

client = TestClient(app)


def _assert_contains_text(messages, expected_substring: str):
    """Busca expected_substring (minúsculas) en algún mensaje.text."""
    expected_substring = expected_substring.lower()
    for m in messages:
        text = (m.get("text") or "").lower()
        if expected_substring in text:
            return True
    return False


@pytest.fixture
def rasa_mock():
    """Mock general de la URL de Rasa."""
    with respx.mock(assert_all_called=True) as respx_mock:
        yield respx_mock


def test_estado_estudiante_sin_token_pide_autenticacion(rasa_mock):
    """
    Escenario:
      - Usuario anónimo (sin Authorization) pide /estado_estudiante.
    Criterio de aceptación:
      - Backend llama a Rasa con metadata.auth.hasToken=False.
      - La respuesta que vuelve al cliente contiene mensaje tipo
        “debes iniciar sesión / necesitas estar autenticado”.
    """
    # Simulamos que Rasa responde con un mensaje de "necesitas iniciar sesión"
    mock_call = rasa_mock.post(settings.rasa_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json=[
                {
                    "recipient_id": "web-anon",
                    "text": "Para continuar necesito que inicies sesión.",
                }
            ],
        )
    )

    payload = {
        "sender": "web-anon",
        "message": "/estado_estudiante",
        "metadata": {},
    }
    r = client.post("/chat", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)

    # El backend sí llamó a Rasa
    assert mock_call.called

    # Validamos que metadata.auth.hasToken=False se haya enviado
    sent_json = mock_call.calls.last.request.json()
    auth_meta = (sent_json.get("metadata") or {}).get("auth", {})
    assert auth_meta.get("hasToken") is False

    # Y que el mensaje de vuelta mencione login/autenticación
    assert _assert_contains_text(
        data,
        "inicies sesión"
    ) or _assert_contains_text(
        data,
        "autenticad"
    ), f"Respuesta no contiene mensaje de autenticación: {data}"


def test_ver_certificados_con_token_no_pide_autenticacion(rasa_mock):
    """
    Escenario:
      - Usuario con token llama /ver_certificados.
    Criterio de aceptación:
      - metadata.auth.hasToken=True hacia Rasa.
      - La respuesta que vuelve NO es un mensaje de 'necesitas iniciar sesión'
        sino algo tipo 'lista de certificados'.
    """
    mock_call = rasa_mock.post(settings.rasa_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json=[
                {
                    "recipient_id": "user123",
                    "text": "Aquí tienes tu lista de certificados (demo).",
                }
            ],
        )
    )

    fake_token = "Bearer DEMO_TOKEN"
    payload = {
        "sender": "user123",
        "message": "/ver_certificados",
        "metadata": {},
    }
    r = client.post("/chat", json=payload, headers={"Authorization": fake_token})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

    assert mock_call.called
    sent_json = mock_call.calls.last.request.json()
    auth_meta = (sent_json.get("metadata") or {}).get("auth", {})
    assert auth_meta.get("hasToken") is True

    # Aseguramos que no sea el típico mensaje de "inicia sesión"
    assert not _assert_contains_text(
        data,
        "inicies sesión"
    ), f"El bot sigue pidiendo login pese a tener token: {data}"
