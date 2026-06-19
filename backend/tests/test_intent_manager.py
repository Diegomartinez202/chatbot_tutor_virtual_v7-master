# backend/test/test_intent_manager.py
"""
Tests unitarios directos sobre backend.services.intent_manager.

Estos NO pasan por HTTP ni dependen de auth.
Asumen que intent_manager trabaja sobre una fuente de datos
(archivo/DB) y expone las funciones:

    - guardar_intent(data: dict)
    - intent_ya_existe(nombre: str) -> bool
    - eliminar_intent(nombre: str)
    - actualizar_intent(nombre: str, data: dict) -> dict

Si la firma real difiere, lo ajustamos luego.
"""

import pytest
from backend.services import intent_manager


@pytest.fixture
def intent_data():
    return {
        "intent": "saludo_test_pytest",
        "examples": ["hola", "buenas"],
        "responses": ["Hola, ¿en qué puedo ayudarte?"],
    }


def test_guardar_y_eliminar_intent(intent_data):
    # Guardar
    intent_manager.guardar_intent(intent_data)
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is True

    # Eliminar
    intent_manager.eliminar_intent(intent_data["intent"])
    assert intent_manager.intent_ya_existe(intent_data["intent"]) is False


def test_actualizar_intent(intent_data):
    # Crear primero
    intent_manager.guardar_intent(intent_data)

    new_data = {
        "examples": ["qué tal", "hello"],
        "responses": ["¡Hola, prueba actualizada!"],
    }
    updated = intent_manager.actualizar_intent(intent_data["intent"], new_data)

    # Validaciones flexibles
    assert updated["intent"] == intent_data["intent"]
    # Allow either message with checkmark or wording similar
    msg = (updated.get("message") or "").lower()
    assert "actualiz" in msg or "✅" in msg

    # Limpieza
    intent_manager.eliminar_intent(intent_data["intent"])

