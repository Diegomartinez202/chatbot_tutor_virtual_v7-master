# backend/test/test_stats.py
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_admin_stats(client: AsyncClient, admin_auth_override):
    """
    Stats para admin: /api/admin/stats
    Esperamos llaves como total_logs e intents_distintos (nombres flexibles).
    """
    r = await client.get(
        "/api/admin/stats",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()

    # Campos mínimos esperados (puedes ajustar nombres si cambian)
    assert any(k in data for k in ("total_logs", "logs_total", "total")), data
    assert any(
        k in data for k in ("intents_distintos", "unique_intents", "intents")
    ), data

    # Si existen, deben ser enteros
    if "total_logs" in data:
        assert isinstance(data["total_logs"], int)
    if "intents_distintos" in data:
        assert isinstance(data["intents_distintos"], int)


@pytest.mark.anyio
async def test_get_dashboard_stats(client: AsyncClient, admin_auth_override):
    """
    Stats de dashboard general: /api/stats
    Validamos estructura general de los campos esperados.
    """
    r = await client.get(
        "/api/stats",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()

    # Claves típicas del dashboard
    assert "total_conversaciones" in data
    assert "intents_mas_usados" in data
    assert "usuarios_por_rol" in data
    assert "actividad_por_dia" in data

    assert isinstance(data["intents_mas_usados"], list)
    assert isinstance(data["usuarios_por_rol"], list)
    assert isinstance(data["actividad_por_dia"], list)
