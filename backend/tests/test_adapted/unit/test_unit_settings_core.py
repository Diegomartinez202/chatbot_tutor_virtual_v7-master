# backend/test/test_adapted/unit/test_unit_settings_core.py

"""
Pruebas unitarias/smoke sobre la configuración base (Settings core).

Objetivo:
    Verificar que los parámetros esenciales del backend del Chatbot Tutor Virtual
    (URL de Rasa, configuración de MongoDB, claves JWT) estén presentes y con
    un formato mínimamente válido, sin depender de Zajuna ni del panel admin.

Estas pruebas se diseñan de forma defensiva para soportar variaciones
en nombres de atributos (mongo_url / mongodb_url / mongo_uri, etc.).
"""

from backend.config.settings import settings


def _get_any_attr(obj, names):
    """Devuelve el primer atributo existente de la lista o None."""
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def test_rasa_url_core_config():
    """
    Verifica que exista una URL base hacia Rasa.

    Criterios:
    - Debe haber algún atributo tipo rasa_url / rasa_rest_url.
    - Debe comenzar por http.
    """
    url = _get_any_attr(settings, ["rasa_url", "rasa_rest_url", "rasa_rest_webhook"])
    assert url is not None, "No se encontró ninguna URL de Rasa en settings."
    assert isinstance(url, str)
    assert url.startswith("http"), f"URL de Rasa inválida: {url!r}"


def test_mongo_core_config():
    """
    Verifica que exista una cadena de conexión a MongoDB.

    Criterios:
    - Debe existir al menos uno de los atributos típicos para Mongo.
    - Debe contener el esquema 'mongodb://'.
    """
    mongo_url = _get_any_attr(
        settings,
        ["mongo_url", "mongodb_url", "mongo_uri", "mongo_uri_full"],
    )
    assert mongo_url is not None, "No se encontró configuración de Mongo en settings."
    assert isinstance(mongo_url, str)
    assert "mongodb://" in mongo_url, f"Cadena MongoDB inesperada: {mongo_url!r}"


def test_jwt_core_config():
    """
    Verifica que la configuración JWT básica esté presente.

    Criterios:
    - SECRET_KEY / secret_key no vacía.
    - Algoritmo JWT definido (ej: HS256).
    """
    secret = _get_any_attr(settings, ["secret_key", "jwt_secret", "jwt_secret_key"])
    algo = _get_any_attr(settings, ["jwt_algorithm", "jwt_alg"])

    assert secret, "SECRET_KEY / jwt_secret no está definido en settings."
    assert isinstance(secret, str)
    assert len(secret) >= 8  # mínimo razonable para entorno de pruebas

    assert algo, "Algoritmo JWT no definido en settings."
    assert isinstance(algo, str)
    assert algo.upper().startswith("HS") or algo.upper().startswith("RS")
