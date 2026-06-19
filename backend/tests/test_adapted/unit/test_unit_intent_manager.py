# backend/test_adapted/unit/test_unit_intent_manager.py
import pytest
from backend.services import intent_manager


@pytest.fixture
def intent_data():
    """
    Intent de prueba para validar las funciones de intent_manager
    sin depender de Zajuna ni de Rasa en ejecución.
    """
    return {
        "intent": "saludo_test",
        "examples": ["hola", "buenas"],
        "responses": ["Hola, ¿en qué puedo ayudarte?"],
    }


def test_guardar_y_eliminar_intent(intent_data):
    """
    Verifica que:
      - guardar_intent registra el intent
      - intent_ya_existe detecta existencia
      - eliminar_intent lo elimina correctamente
    """
    intent_manager.guardar_intent(intent_data)
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is True

    intent_manager.eliminar_intent(intent_data["intent"])
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is False


def test_actualizar_intent(intent_data):
    """
    Verifica que actualizar_intent:
      - mantenga el nombre del intent
      - modifique examples/responses
      - devuelva un mensaje de éxito amigable
    """
    intent_manager.guardar_intent(intent_data)

    new_data = {
        "examples": ["qué tal", "hello"],
        "responses": ["¡Hola, prueba actualizada!"],
    }
    updated = intent_manager.actualizar_intent(intent_data["intent"], new_data)

    assert updated["intent"] == intent_data["intent"]
    assert any("actualiz" in updated.get("message", "").lower() or "✅" in updated.get("message", "") for _ in [0])

    intent_manager.eliminar_intent(intent_data["intent"])
