import pytest
from backend.services import intent_manager

@pytest.fixture
def intent_data():
    return {
        "intent": "saludo_test",
        "examples": ["hola", "buenas"],
        "responses": ["Hola, ¿en qué puedo ayudarte?"]
    }

def test_guardar_y_eliminar_intent(intent_data):
    intent_manager.guardar_intent(intent_data)
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is True

    intent_manager.eliminar_intent(intent_data["intent"])
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is False

def test_actualizar_intent(intent_data):
    intent_manager.guardar_intent(intent_data)
    new_data = {
        "examples": ["qué tal", "hello"],
        "responses": ["¡Hola, prueba actualizada!"]
    }
    updated = intent_manager.actualizar_intent(intent_data["intent"], new_data)
    assert updated["intent"] == intent_data["intent"]
    assert "✅" in updated["message"]

    intent_manager.eliminar_intent(intent_data["intent"])
