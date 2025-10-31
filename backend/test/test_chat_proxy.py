# backend/tests/test_chat_proxy.py
import os
import pytest

RASA_URL = os.getenv("RASA_REST_URL", "http://rasa:5005/webhooks/rest/webhook")

@pytest.mark.anyio
async def test_demo_endpoint_ok(client):
    resp = await client.post("/chat/demo", json={"message": "Hola"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any("text" in m for m in data)

@pytest.mark.anyio
async def test_rasa_proxy_ok(client):
    """
    Test de integración real: requiere que el contenedor 'rasa' esté healthy.
    Si no está disponible, el test falla con mensaje claro.
    """
    payload = {
        "sender": "pytest-user-1",
        "message": "hola",
        "metadata": {"auth": {"hasToken": True}, "ui": {"from": "pytest"}}
    }
    resp = await client.post("/chat/rasa/rest/webhook", json=payload)

    # Si el proxy devuelve dict con "error", es que no llegó a Rasa
    if resp.headers.get("content-type", "").startswith("application/json"):
        data = resp.json()
    else:
        data = None

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {data}"
    assert isinstance(data, list), f"Respuesta no es lista: {data}"
    # Rasa debería responder al menos con 0..n mensajes; si 0, no rompe
    # Pero validamos que no sea un dict de error del proxy
    # (el proxy devuelve {"error": "..."} en caso de fallo)
    assert not isinstance(data, dict), f"Proxy devolvió error: {data}"

@pytest.mark.anyio
async def test_rasa_proxy_metadata_inject(client, monkeypatch):
    """
    Verifica que el proxy inyecte metadata.ui.proxied=True si falta.
    No valida contra Rasa; solo que el backend no crashea.
    """
    payload = {
        "sender": "pytest-user-2",
        "message": "hola"
        # sin metadata a propósito
    }
    resp = await client.post("/chat/rasa/rest/webhook", json=payload)
    # Si Rasa no está, el proxy responde {"error": "..."} pero no 500.
    assert resp.status_code == 200
