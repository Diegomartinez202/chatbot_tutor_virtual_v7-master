# backend/test/test_adapted/functional/test_func_chat_auth_sensitive.py

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from backend.main import app
from backend.config.settings import settings

client = TestClient(app)


@pytest.fixture
def rasa_mock():
    """
    Mock de la URL de Rasa usada por el backend.
    """
    with respx.mock(assert_all_called=True) as respx_mock:
        yield respx_mock


def test_estado_estudiante_sin_token_pide_autenticacion(rasa_mock):
    """
    Escenario:
      - Usuario anónimo (sin Authorization) pide /estado_estudiante.

    Criterio de aceptación:
      - El backend responde 200.
      - La respuesta contiene un mensaje indicando que debe iniciar sesión
        o estar autenticado.
      - El backend llama a Rasa (mock_call.called == True).
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
    textos = " ".join(m.get("text", "") for m in data)
    # Algún mensaje debe mencionar que necesita iniciar sesión
    assert "inicies sesión" in textos or "autenticado" in textos

    # El backend sí llamó a Rasa
    assert mock_call.called


def test_ver_certificados_con_token_no_pide_autenticacion(rasa_mock):
    """
    Escenario:
      - Usuario con token llama /ver_certificados.

    Criterio de aceptación:
      - El backend responde 200.
      - La respuesta NO es un mensaje de 'necesitas iniciar sesión'
        sino algo tipo 'lista de certificados'.
      - El backend llama a Rasa (mock_call.called == True).
    """
    mock_call = rasa_mock.post(settings.rasa_url).mock(
        return_value=httpx.Response(
            status_code=200,
            json=[
                {
                    "recipient_id": "user123",
                    "text": "Aquí está la lista de tus certificados.",
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
    textos = " ".join(m.get("text", "") for m in data)

    # No debería ser un mensaje de "inicia sesión"
    assert "inicies sesión" not in textos
    assert "autenticado" not in textos

    # El backend debe haber llamado a Rasa
    assert mock_call.called

