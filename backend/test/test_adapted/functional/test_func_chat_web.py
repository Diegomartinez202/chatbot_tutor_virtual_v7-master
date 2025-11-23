# backend/test/test_adapted/functional/test_func_chat_web.py

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_chat_demo_endpoint_ok():
    """
    Verifica que /chat/demo responde 200 y devuelve una lista de mensajes.

    Este endpoint es totalmente independiente de Rasa/Zajuna y sirve como
    prueba funcional básica del chatbot web embebido.
    """
    r = client.post("/chat/demo", json={"message": "Hola"})
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    # No exigimos texto concreto, solo que haya al menos un mensaje
    assert len(data) >= 1


def test_chat_health_endpoint_ok():
    """
    Verifica que /chat/health responde 200 y expone un estado básico.

    En este proyecto, cuando Rasa no está disponible, el endpoint devuelve:
      {
        "ok": false,
        "error": "...",
        "rasa_url": "http://rasa:5005/webhooks/rest/webhook"
      }

    Aceptamos tanto el caso ok=True (Rasa levantado) como ok=False (Rasa caído),
    siempre que:
      - el HTTP sea 200
      - exista la clave 'ok'
      - exista 'rasa_url'
      - si ok == False, haya un campo de error descriptivo.
    """
    r = client.get("/chat/health")
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, dict)

    # Claves mínimas esperadas
    assert "ok" in data
    assert "rasa_url" in data

    # Si Rasa está caído (ok == False), debe haber mensaje de error
    if data.get("ok") is False:
        assert "error" in data and isinstance(data["error"], str)

    # Si en algún entorno se añade un campo "status", lo validamos de forma laxa
    status = data.get("status")
    if isinstance(status, str):
        assert status.lower() in {"ok", "healthy", "error"}


def test_chat_proxy_no_crashea_sin_rasa():
    """
    Escenario: se llama /chat (proxy hacia Rasa).

    Restricción del proyecto:
      - Rasa puede no estar disponible en entornos de prueba.
    Objetivo del test:
      - El backend NO debe lanzar 500 ni tronar; debe responder de forma
        controlada:
          * 200 con lista de mensajes, o
          * 200 con {"error": "..."} o similar, o
          * 502 Bad Gateway con mensaje de error JSON/Texto.
    """
    payload = {
        "sender": "pytest-user",
        "message": "hola",
        "metadata": {},
    }
    r = client.post("/chat", json=payload)

    # Aceptamos 200 (Rasa OK) o 502 (Rasa caído). Lo importante: no 500.
    assert r.status_code in (200, 502)

    # Si es 200: lista de mensajes o dict de error
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, (list, dict))

    # Si es 502: debe haber al menos un mensaje de error entendible
    else:
        ct = r.headers.get("content-type", "")
        if ct.startswith("application/json"):
            body = r.json()
            assert isinstance(body, dict)
            # Aceptamos mensajes de error con 'detail' o 'error'
            assert "detail" in body or "error" in body
        else:
            # Si fuera HTML/texto plano, al menos que contenga "Error"
            assert "Error" in r.text or "error" in r.text
