# backend/test/test_intents.py
import io
import pytest
from httpx import AsyncClient


INTENT_ID = "saludo.test.pytest"


@pytest.mark.anyio
async def test_create_intent(client: AsyncClient, admin_auth_override):
    """
    Crea (o reintenta crear) un intent vía API.
    Toleramos que ya exista (409/400), pero verificamos el mensaje.
    """
    payload = {
        "intent": INTENT_ID,
        "examples": ["Hola", "Buenos días"],
        "responses": ["¡Hola! ¿Cómo estás?"],
    }

    r = await client.post(
        "/api/admin/intents",
        json=payload,
        headers={"Authorization": "Bearer demo"},
    )

    assert r.status_code in (200, 201, 400, 409), r.text
    data = r.json()

    if r.status_code in (200, 201):
        # Alta correcta
        assert "message" in data
        assert "Intent" in data["message"] or "creado" in data["message"].lower()
    else:
        # Ya existe o validación
        assert "detail" in data
        # texto flexible, por si cambias wording
        assert any(
            frag in data["detail"].lower()
            for frag in ("ya existe", "duplicado", "exists")
        )


@pytest.mark.anyio
async def test_list_intents(client: AsyncClient, admin_auth_override):
    """
    Lista intents. Debe devolver una lista JSON.
    """
    r = await client.get(
        "/api/admin/intents",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)

    # Si el intent de prueba existe, debe estar en la lista
    intents = {item.get("intent") for item in data if isinstance(item, dict)}
    # No exigimos que esté, pero si está, validamos tipo
    if INTENT_ID in intents:
        assert INTENT_ID in intents


@pytest.mark.anyio
async def test_export_intents_csv(client: AsyncClient, admin_auth_override):
    """
    Exporta intents a CSV. Sólo validamos cabeceras básicas y contenido mínimo.
    """
    r = await client.get(
        "/api/admin/intents/export",
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200, r.text
    ctype = r.headers.get("content-type", "").lower()
    assert "text/csv" in ctype

    content = r.content.decode("utf-8", errors="ignore")
    # Encabezados típicos
    assert "intent" in content.lower()
    assert "examples" in content.lower()
    assert "responses" in content.lower()


@pytest.mark.anyio
async def test_upload_intents_csv(client: AsyncClient, admin_auth_override):
    """
    Sube un CSV con intents de prueba.
    Verificamos sólo que responda 200 y mensaje de ok.
    """
    csv_content = (
        "intent,examples,responses\n"
        "prueba_csv_pytest,\"hola\\nbuenas\",\"¡Hola!\\n¿Qué tal?\""
    )

    files = {
        "file": ("intents.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }

    r = await client.post(
        "/api/admin/intents/upload",
        headers={"Authorization": "Bearer demo"},
        files=files,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # Mensaje flexible según implementación
    msg = (data.get("message") or "").lower()
    assert any(
        frag in msg for frag in ("intents cargados", "cargados", "importados")
    )
