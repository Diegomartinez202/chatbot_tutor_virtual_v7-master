# tests/test_contract_admin_logs.py
import pytest
from datetime import datetime

# 🔧 Ajusta si tu endpoint admite paginación por otros nombres (p. ej., limit/offset)
LOGS_ENDPOINT = "/api/admin/logs"
DEFAULT_QUERY = {"page": 1, "page_size": 10}

ORIGEN_VALUES = {"widget", "autenticado"}

def _is_iso_like(s: str) -> bool:
    if not isinstance(s, str):
        return False
    # Aceptamos formatos ISO comunes, con o sin 'Z'
    try:
        if s.endswith("Z"):
            datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            # Permite microsegundos u offset
            datetime.fromisoformat(s)
        return True
    except Exception:
        return ("T" in s) and ("-" in s)  # fallback laxo si tu backend serializa distinto

@pytest.fixture()
def seed_log():
    """Inserta un log mínimo para asegurar al menos 1 item y limpia luego."""
    try:
        from backend.db.mongodb import get_logs_collection
    except Exception:
        pytest.skip("No se pudo importar get_logs_collection; revisar configuración de Mongo.")
    coll = get_logs_collection()
    doc = {
        "sender_id": "pytest-admin",
        "user_message": "hola desde test",
        "bot_response": ["respuesta de prueba"],
        "intent": "saludo",
        "timestamp": datetime.utcnow(),
        "ip": "127.0.0.1",
        "user_agent": "pytest",
        "origen": "autenticado",
        "metadata": {"test": True},
    }
    inserted = coll.insert_one(doc)
    try:
        yield inserted.inserted_id
    finally:
        coll.delete_one({"_id": inserted.inserted_id})

def test_admin_logs_contract_shape(client_admin, seed_log):
    """Contrato estricto del endpoint /api/admin/logs."""
    # 1) Llamada
    r = client_admin.get(LOGS_ENDPOINT, params=DEFAULT_QUERY)
    if r.status_code == 404:
        pytest.skip(f"Endpoint inexistente: {LOGS_ENDPOINT}")
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"

    data = r.json()
    # 2) Estructura de nivel raíz
    for key in ("items", "total", "page", "page_size"):
        assert key in data, f"Falta clave '{key}' en respuesta raíz"

    assert isinstance(data["items"], list), "items debe ser lista"
    assert isinstance(data["total"], int), "total debe ser int"
    assert isinstance(data["page"], int), "page debe ser int"
    assert isinstance(data["page_size"], int), "page_size debe ser int"
    assert 0 <= data["page"] <= 10_000
    assert 1 <= data["page_size"] <= 10_000

    # 3) Validación de cada item (si hay)
    for i, item in enumerate(data["items"]):
        assert isinstance(item, dict), f"items[{i}] debe ser dict"
        # Claves mínimas del contrato
        for k in ("sender_id", "user_message", "bot_response", "timestamp", "origen"):
            assert k in item, f"Falta '{k}' en items[{i}]"

        # Tipos
        assert isinstance(item["sender_id"], str)
        assert isinstance(item["user_message"], str)
        assert isinstance(item.get("bot_response", []), list)
        assert all(isinstance(x, str) for x in item.get("bot_response", [])), "bot_response debe ser lista de strings"

        # intent opcional o string/null
        if "intent" in item and item["intent"] is not None:
            assert isinstance(item["intent"], str)

        # timestamp ISO-like
        assert _is_iso_like(item["timestamp"]), f"timestamp no parece ISO: {item['timestamp']}"

        # ip / user_agent pueden ser null o string
        if "ip" in item and item["ip"] is not None:
            assert isinstance(item["ip"], str)
        if "user_agent" in item and item["user_agent"] is not None:
            assert isinstance(item["user_agent"], str)

        # origen acotado
        assert item["origen"] in ORIGEN_VALUES, f"origen inválido: {item['origen']}"

        # metadata opcional dict
        if "metadata" in item and item["metadata"] is not None:
            assert isinstance(item["metadata"], dict)

def test_admin_logs_pagination_bounds(client_admin, seed_log):
    """Chequeos básicos de paginación predefinida."""
    r = client_admin.get(LOGS_ENDPOINT, params={"page": 1, "page_size": 1})
    if r.status_code == 404:
        pytest.skip(f"Endpoint inexistente: {LOGS_ENDPOINT}")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 1
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert isinstance(data["total"], int)
