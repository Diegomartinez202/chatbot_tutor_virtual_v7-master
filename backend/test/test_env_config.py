# backend/tests/test_env_config.py
from config import MONGO_URI, MONGO_DB_NAME, JWT_SECRET, JWT_EXPIRATION_MINUTES, RASA_SERVER_URL

def test_env_variables():
    assert MONGO_URI is not None, "MONGO_URI no está definido"
    assert MONGO_DB_NAME is not None, "MONGO_DB_NAME no está definido"
    assert JWT_SECRET is not None, "JWT_SECRET no está definido"
    assert JWT_EXPIRATION_MINUTES > 0, "JWT_EXPIRATION_MINUTES debe ser mayor a 0"
    assert RASA_SERVER_URL.startswith("http"), "RASA_SERVER_URL debe comenzar con http"

