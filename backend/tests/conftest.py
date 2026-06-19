# backend/test/conftest.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.main import app as app_instance

try:
    # Si existe create_app, lo usamos; si no, usamos app directamente
    from backend.main import create_app  # type: ignore
except ImportError:
    create_app = None  # type: ignore


@pytest.fixture(scope="session")
def app():
    if create_app is not None:
        return create_app()
    return app_instance


@pytest.fixture(scope="session")
def client(app):
    """
    Cliente síncrono para la mayoría de tests (TestClient).
    """
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """
    Cliente async httpx para tests con pytest.mark.asyncio.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
