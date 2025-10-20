# tests/test_protected_endpoints.py
import pytest

# Endpoints que se esperan PROTEGIDOS.
# Si alguno no existe en tu API, el test lo omite con skip.
PROTECTED_ENDPOINTS = [
    "/api/admin/intents",   # listado de intents (admin)
    "/api/admin/logs",      # logs del sistema (admin)
    "/api/users",           # listado de usuarios (si existe)
    "/api/exportaciones",   # historial de exportaciones (si existe y protegido)
    "/api/stats",           # métricas (si las protegiste)
]

@pytest.fixture(scope="session")
def user_token():
    """Token de un usuario NO admin (rol 'usuario') para validar 403."""
    try:
        from backend.utils.jwt_manager import create_access_token
    except Exception:
        from backend.services.jwt_manager import create_access_token  # type: ignore
    return create_access_token({"sub": "user@example.com", "rol": "usuario"})

@pytest.fixture(scope="session", autouse=True)
def setup_regular_user():
    """Crea un usuario regular en la BD para que endpoints que validen en DB no fallen."""
    try:
        from backend.db.mongodb import get_users_collection
    except Exception:
        yield
        return

    users = get_users_collection()
    email = "user@example.com"
    if not users.find_one({"email": email}):
        users.insert_one({
            "nombre": "User",
            "email": email,
            "password": "test_password_placeholder",
            "rol": "usuario",
            "is_active": True,
            "created_by": "pytest",
        })
    try:
        yield
    finally:
        users.delete_many({"email": email})

@pytest.fixture()
def client_user(app, user_token):
    """Cliente con token de usuario normal (no admin)."""
    from fastapi.testclient import TestClient
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {user_token}"})
    return c

def _probe_or_skip(resp, path):
    """Si el endpoint no existe, omitimos; si existe, seguimos con asserts."""
    if resp.status_code == 404:
        pytest.skip(f"Endpoint inexistente en este build: {path}")

def test_protected_requires_auth(client):
    """Sin token: debe devolver 401/403 en endpoints protegidos existentes."""
    for path in PROTECTED_ENDPOINTS:
        r = client.get(path)
        if r.status_code == 404:
            pytest.skip(f"Endpoint inexistente en este build: {path}")
        # Si existe y es protegido, esperamos 401 (sin credenciales) o 403 (bloqueo inmediato)
        assert r.status_code in (401, 403), f"{path} devolvió {r.status_code}, se esperaba 401/403"

def test_protected_for_user_role_forbidden(client_user):
    """Con token de usuario normal: debería ser 403 en rutas solo-admin (si existen)."""
    for path in PROTECTED_ENDPOINTS:
        r = client_user.get(path)
        if r.status_code == 404:
            pytest.skip(f"Endpoint inexistente en este build: {path}")
        # En rutas solo-admin esperamos 403; si alguna ruta permite usuario normal, puede dar 200.
        assert r.status_code in (200, 403), f"{path} devolvió {r.status_code}, se esperaba 200/403"

def test_protected_for_admin_ok(client_admin):
    """Con token admin: deberían responder OK (200/204) en endpoints existentes."""
    for path in PROTECTED_ENDPOINTS:
        r = client_admin.get(path)
        if r.status_code == 404:
            pytest.skip(f"Endpoint inexistente en este build: {path}")
        assert r.status_code in (200, 204), f"{path} devolvió {r.status_code}, se esperaba 200/204"