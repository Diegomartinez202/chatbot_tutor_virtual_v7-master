# backend/test_adapted/functional/test_func_chat_web.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_demo_chat_responde_lista_de_mensajes():
    """
    Escenario: usuario anónimo usa el endpoint de demo /chat/demo.

    Criterio de aceptación:
      - HTTP 200
      - Respuesta es una lista
      - Al menos un mensaje tiene campo "text"
    """
    r = client.post("/chat/demo", json={"message": "Hola"})
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list), f"Respuesta no es lista: {data}"
    assert any("text" in m for m in data), "Ningún mensaje contiene 'text'"


def test_chat_health_endpoint_ok():
    """
    Verifica que /chat/health expone un estado básico del chatbot.
    No depende de Rasa ni Zajuna.
    """
    r = client.get("/chat/health")
    assert r.status_code == 200

    data = r.json()
    # Aceptamos distintas convenciones pero debe indicar estado sano
    assert data.get("status", "").lower() in {"ok", "healthy"}


def test_chat_proxy_no_crashea_sin_rasa():
    """
    Escenario: se llama /chat (proxy hacia Rasa).

    Dado que en algunos entornos Rasa puede no estar disponible,
    el backend no debe lanzar 500 sino:
      - 200 con lista de mensajes, o
      - 200 con {"error": "..."} indicando fallo de conexión.

    Esto respeta la restricción de dependencia externa.
    """
    payload = {
        "sender": "pytest-user",
        "message": "hola",
        "metadata": {},
    }
    r = client.post("/chat", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert isinstance(
        data, (list, dict)
    ), f"Respuesta inesperada: tipo={type(data)}, valor={data}"

    # Si es dict, esperamos que sea un mensaje de error controlado del proxy
    if isinstance(data, dict):
        assert "error" in data, "Dict devuelto por /chat debería contener 'error'"
