# backend/test/test_logs.py
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_listar_archivos_log(client: AsyncClient, admin_auth_override):
    """
    Lista de archivos de log vía /api/admin/logs.
    Debe devolver 200 y una lista (aunque esté vacía).
    """
    r = await client.get(
        "/api/admin/logs",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_descargar_log_invalido(client: AsyncClient, admin_auth_override):
    """
    Probar que un nombre de log inválido sea rechazado con 400 o 404
    (según tu implementación).
    """
    r = await client.get(
        "/api/admin/logs/../../hack.txt",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code in (400, 404), r.text


@pytest.mark.anyio
async def test_exportar_logs_csv(client: AsyncClient, admin_auth_override):
    """
    Exportación de logs a CSV. Sólo verificamos content-type y status.
    """
    r = await client.get(
        "/api/admin/logs/export",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    ctype = r.headers.get("content-type", "").lower()
    assert "text/csv" in ctype


@pytest.mark.anyio
async def test_contar_mensajes_no_leidos(client: AsyncClient, admin_auth_override):
    """
    Cuenta de mensajes no leídos. La estructura puede variar,
    pero al menos debe contener alguna clave tipo 'unread' o similar.
    """
    r = await client.get(
        "/api/logs/unread_count",
        params={"user_id": "pytest_user"},
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # aceptamos varias formas de llamar al campo
    assert any(k in data for k in ("unread", "unread_count", "count"))


@pytest.mark.anyio
async def test_marcar_mensajes_leidos(client: AsyncClient, admin_auth_override):
    """
    Marca mensajes como leídos. Esperamos 200 y algún contador de filas actualizadas.
    """
    r = await client.post(
        "/api/logs/mark_read",
        params={"user_id": "pytest_user"},
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert any(
        k in data for k in ("updated_count", "updated", "ok")
    ), f"Respuesta inesperada: {data}"
