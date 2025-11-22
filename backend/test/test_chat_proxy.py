# backend/test/test_chat_proxy.py
import os
import pytest

RASA_URL = os.getenv("RASA_REST_URL", "http://rasa:5005/webhooks/rest/webhook")


@pytest.mark.asyncio
async def test_demo_endpoint_ok(async_client):
    resp = await async_client.post("/chat/demo", json={"message": "Hola"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any("text" in m for m in data)


@pytest.mark.asyncio
async def test_rasa_proxy_ok(async_client):
    """
    Requiere que el contenedor 'rasa' esté healthy, o que tu backend maneje bien el error.
    """
    payload = {
        "sender": "pytest-user-1",
        "message": "hola",
        "metadata": {"auth": {"hasToken": True}, "ui": {"from": "pytest"}},
    }
    resp = await async_client.post("/chat/rasa/rest/webhook", json=payload)

    if resp.headers.get("content-type", "").startswith("application/json"):
        data = resp.json()
    else:
        data = None

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {data}"
    assert isinstance(data, list), f"Respuesta no es lista: {data}"
    assert not isinstance(data, dict), f"Proxy devolvió error: {data}"


@pytest.mark.asyncio
async def test_rasa_proxy_metadata_inject(async_client):
    payload = {
        "sender": "pytest-user-2",
        "message": "hola",
        # sin metadata a propósito
    }
    resp = await async_client.post("/chat/rasa/rest/webhook", json=payload)
    assert resp.status_code == 200
