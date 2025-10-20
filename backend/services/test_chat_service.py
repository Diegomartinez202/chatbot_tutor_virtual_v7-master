# test/services/test_chat_service.py

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
# 🧪 Test del proxy Rasa
# ============================
@pytest.mark.asyncio
async def test_process_user_message(monkeypatch):
    async def mock_post(url, json):
        async with httpx.AsyncClient(transport=MockTransport()) as client:
            return await client.post(url, json=json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    response = await process_user_message("hola", "test_user")
    assert isinstance(response, list)
    assert response[0]["text"] == "¡Hola! ¿En qué puedo ayudarte?"
    assert response[0]["intent"]["name"] == "saludo"

@pytest.mark.asyncio
async def test_process_user_message_error(monkeypatch):
    async def mock_post(url, json):
        async with httpx.AsyncClient(transport=MockTransport()) as client:
            return await client.post(url, json=json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(Exception) as excinfo:
        await process_user_message("error", "test_user")

    assert "Error" in str(excinfo.value)