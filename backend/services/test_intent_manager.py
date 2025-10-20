# test/services/test_intent_manager.py

import pytest
from backend.services import intent_manager

@pytest.fixture
def intent_data():
    return {
        "intent": "saludo_test",
        "examples": ["hola", "buenas"],
        "responses": ["Hola, ¿en qué puedo ayudarte?"]
    }

@pytest.fixture
def updated_data():
    return {
        "examples": ["hello", "qué tal"],
        "responses": ["¡Hola, mensaje actualizado!"]
    }

def test_guardar_intent(intent_data):
    result = intent_manager.guardar_intent(intent_data)
    assert "✅" in result["message"]
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is True

def test_actualizar_intent(intent_data, updated_data):
    # Asegurarse de que el intent esté creado primero
    if not intent_manager.intent_ya_existe(intent_data["intent"]):
        intent_manager.guardar_intent(intent_data)

    result = intent_manager.actualizar_intent(intent_data["intent"], updated_data)
    assert "✅" in result["message"]
    assert result["examples"] == updated_data["examples"]
    assert result["responses"] == updated_data["responses"]

def test_eliminar_intent(intent_data):
    if not intent_manager.intent_ya_existe(intent_data["intent"]):
        intent_manager.guardar_intent(intent_data)

    result = intent_manager.eliminar_intent(intent_data["intent"])
    assert "🗑️" in result["message"]
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is False