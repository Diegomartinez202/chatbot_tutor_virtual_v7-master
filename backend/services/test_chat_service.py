# =====================================================
# # test/services/test_chat_service.py
# =====================================================
import pytest
import httpx
from httpx import Response, Request

from backend.services.chat_service import process_user_message

# ============================
# 🧪 Mock de transporte HTTP
# ============================
class MockTransport(httpx.BaseTransport):
    def handle_request(self, request: Request) -> Response:
        body = request.read()
        if b'"message": "hola"' in body:
            return Response(
                status_code=200,
                json=[{"text": "¡Hola! ¿En qué puedo ayudarte?", "intent": {"name": "saludo"}}]
            )
        elif b'"message": "error"' in body:
            return Response(status_code=500, json={"detail": "Error interno"})
        else:
            return Response(status_code=404, json={"detail": "No encontrado"})


# ============================
# 🧪 Helper AsyncClient falso
# ============================
class FakeAsyncClient:
    """
    Emula httpx.AsyncClient con el transporte mock.
    Respeta el contexto async y la firma de .post(url, *, json=None, headers=None, **kwargs)
    """
    def __init__(self, *_, **__):
        self._client = httpx.AsyncClient(transport=MockTransport())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()

    async def post(self, url, *, json=None, headers=None, **kwargs):
        return await self._client.post(url, json=json, headers=headers, **kwargs)


# ============================
# 🧪 Test del proxy Rasa
# ============================
@pytest.mark.asyncio
async def test_process_user_message(monkeypatch):
    # Parcheamos toda la clase AsyncClient por nuestro fake
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = await process_user_message("hola", "test_user")
    assert isinstance(response, list)
    assert response[0]["text"] == "¡Hola! ¿En qué puedo ayudarte?"
    assert response[0]["intent"]["name"] == "saludo"


@pytest.mark.asyncio
async def test_process_user_message_error(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(Exception):
        await process_user_message("error", "test_user")
