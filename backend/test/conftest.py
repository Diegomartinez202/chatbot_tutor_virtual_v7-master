# backend/tests/conftest.py
import os
import pytest
from httpx import AsyncClient
from backend.main import create_app

@pytest.fixture(scope="session")
def anyio_backend():
    # Permite tests async con httpx + pytest-anyio
    return "asyncio"

@pytest.fixture(scope="session")
def app():
    # Instancia única de la app para toda la sesión de tests
    return create_app()

@pytest.fixture
async def client(app):
    # Cliente HTTP async contra la app en memoria (sin red)
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
