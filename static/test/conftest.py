# tests/conftest.py
"""
Fixture global de pytest para configurar el entorno de pruebas:
- Carga opcional de .env.test (antes de importar la app)
- Fuerza flags mínimas de test/CI (desactiva rate limit)
- Defaults seguros para JWT y RASA_URL (si el .env no los define)
- Directorio de logs temporal en CI
- Fixtures: app, client, seed de usuarios (admin/user), tokens y clients con Authorization
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# 1) Cargar .env.test si existe (antes de importar la app)
# ─────────────────────────────────────────────────────────────────────────────
env_test = Path(".env.test")
if env_test.exists():
    load_dotenv(env_test, override=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2) Flags mínimas de entorno para tests/CI
#    (en tu main.py, APP_ENV == "test" desactiva el rate limiter)
# ─────────────────────────────────────────────────────────────────────────────
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("DEBUG", "true")

# Defaults de JWT y Rasa (si tu .env no los define)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault(
    "SECRET_KEY", "tests_secret_please_change_me________________________"
)
os.environ.setdefault("RASA_URL", "http://rasa.local/webhooks/rest/webhook")

# (Opcional) Directorio de logs en CI para evitar escribir en el repo
os.environ.setdefault("LOG_DIR", "/tmp/logs")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _hash_for_tests(plain: str) -> str:
    """
    Intenta usar el hasher real del proyecto; si no, usa bcrypt;
    si tampoco está disponible, devuelve el texto plano (solo tests).
    """
    # a) Tu helper real (si existe)
    try:
        from backend.utils.security import get_password_hash  # pragma: no cover
        return get_password_hash(plain)
    except Exception:
        pass

    # b) bcrypt directo
    try:
        import bcrypt  # pragma: no cover
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception:
        # c) Solo para tests sin login real
        return plain


def _create_token(payload: dict) -> str:
    """
    Genera un access token. Prioriza tu helper, si no usa PyJWT con HS*.
    """
    # a) Tu helper real (si existe)
    try:
        from backend.utils.jwt_manager import create_access_token  # pragma: no cover
        return create_access_token(payload)
    except Exception:
        pass

    try:
        from backend.services.jwt_manager import create_access_token  # pragma: no cover
        return create_access_token(payload)
    except Exception:
        pass

    # b) Fallback: PyJWT con SECRET_KEY y algoritmo de settings/env
    import jwt  # PyJWT

    secret = os.environ.get("SECRET_KEY")
    alg = (os.environ.get("JWT_ALGORITHM") or "HS256").upper()

    claims = {
        **payload,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(claims, secret, algorithm=alg)


# ─────────────────────────────────────────────────────────────────────────────
# 3) App y cliente (fixtures compartidas)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def app():
    # Import tardío para respetar variables de entorno anteriores
    from backend.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# 4) Seed de usuarios: admin + usuario normal (si existe Mongo y la colección)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_seed_users():
    """
    Inserta dos usuarios mínimos para pruebas, si existe la capa de Mongo.
    Si no existe (p.ej. en CI sin DB), la fixture no falla.
    """
    try:
        from backend.db.mongodb import get_users_collection
        users = get_users_collection()
    except Exception:
        # No hay DB configurada o helper no disponible → no se hace seed
        yield
        return

    admin_email = "admin@example.com"
    user_email = "user@example.com"

    # Admin
    if not users.find_one({"email": admin_email}):
        users.insert_one(
            {
                "nombre": "Admin",
                "email": admin_email,
                "password": _hash_for_tests("Admin123!*"),  # hash según tu helper
                "rol": "admin",
                "is_active": True,
                "created_by": "pytest",
            }
        )

    # Usuario normal
    if not users.find_one({"email": user_email}):
        users.insert_one(
            {
                "nombre": "User",
                "email": user_email,
                "password": _hash_for_tests("User123!*"),
                "rol": "usuario",
                "is_active": True,
                "created_by": "pytest",
            }
        )

    try:
        yield
    finally:
        # Limpieza best-effort
        try:
            users.delete_many({"email": {"$in": [admin_email, user_email]}})
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 5) Tokens de conveniencia (admin / user) y clients con Authorization
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def admin_token():
    return _create_token({"sub": "admin@example.com", "rol": "admin"})


@pytest.fixture(scope="session")
def user_token():
    return _create_token({"sub": "user@example.com", "rol": "usuario"})


@pytest.fixture()
def client_admin(app, admin_token):
    from fastapi.testclient import TestClient

    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {admin_token}"})
    return c


@pytest.fixture()
def client_user(app, user_token):
    from fastapi.testclient import TestClient

    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {user_token}"})
    return c
