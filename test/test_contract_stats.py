# tests/test_contract_stats.py
import pytest
from datetime import datetime, timezone, date as date_cls

STATS_ENDPOINT = "/api/stats"

def _today_iso():
    # Fecha UTC "YYYY-MM-DD" (común para agregaciones diarias)
    return datetime.now(timezone.utc).date().isoformat()

def _is_yyyy_mm_dd(s: str) -> bool:
    if not isinstance(s, str) or len(s) != 10:
        return False
    try:
        y, m, d = s.split("-")
        int(y), int(m), int(d)
        return True
    except Exception:
        return False

@pytest.fixture()
def seed_stats():
    """
    Inserta una métrica diaria mínima para garantizar al menos 1 item en /api/stats
    y la limpia al finalizar.
    """
    try:
        from backend.db.mongodb import get_statistics_collection
    except Exception:
        pytest.skip("No se pudo importar get_statistics_collection; revisa tu módulo Mongo.")
    coll = get_statistics_collection()

    today = _today_iso()
    doc = {
        "date": today,  # contrato recomendado: string YYYY-MM-DD
        "messages_count": 7,
        "users_active": 3,
        "intents_top": [{"intent": "saludo", "count": 5}, {"intent": "ayuda", "count": 2}],
        "avg_response_time_ms": 123.4,
        # Campos opcionales que podrías almacenar por día:
        "channels": {"widget": 7, "api": 0},
        "created_by": "pytest",
        "created_at": datetime.now(timezone.utc),
    }

    inserted = coll.insert_one(doc)
    try:
        yield today
    finally:
        coll.delete_one({"_id": inserted.inserted_id})

def test_stats_contract_shape(client_admin, seed_stats):
    """
    Contrato estricto para /api/stats:
    Espera 200 con:
    {
      "items": [ { "date": "YYYY-MM-DD", "messages_count": int, "users_active": int,
                   "intents_top": [{"intent": str, "count": int}, ...],
                   "avg_response_time_ms": number }, ... ],
      "from": "YYYY-MM-DD",
      "to": "YYYY-MM-DD",
      "total_days": int
    }
    """
    r = client_admin.get(STATS_ENDPOINT)
    if r.status_code == 404:
        pytest.skip(f"Endpoint inexistente: {STATS_ENDPOINT}")
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"

    data = r.json()
    for k in ("items", "from", "to", "total_days"):
        assert k in data, f"Falta clave '{k}' en respuesta raíz"

    assert isinstance(data["items"], list), "items debe ser lista"
    assert isinstance(data["total_days"], int), "total_days debe ser int"
    assert _is_yyyy_mm_dd(data["from"]), "from debe ser 'YYYY-MM-DD'"
    assert _is_yyyy_mm_dd(data["to"]), "to debe ser 'YYYY-MM-DD'"

    for i, item in enumerate(data["items"]):
        assert isinstance(item, dict), f"items[{i}] debe ser dict"
        for key in ("date", "messages_count", "users_active", "intents_top", "avg_response_time_ms"):
            assert key in item, f"Falta '{key}' en items[{i}]"

        assert _is_yyyy_mm_dd(item["date"]), f"date inválido en items[{i}]: {item['date']}"
        assert isinstance(item["messages_count"], int), "messages_count debe ser int"
        assert isinstance(item["users_active"], int), "users_active debe ser int"

        # intents_top: lista de objetos {intent:str, count:int}
        intents_top = item["intents_top"]
        assert isinstance(intents_top, list), "intents_top debe ser lista"
        for j, it in enumerate(intents_top):
            assert isinstance(it, dict), f"intents_top[{j}] debe ser dict"
            assert "intent" in it and "count" in it, f"intents_top[{j}] requiere intent y count"
            assert isinstance(it["intent"], str)
            assert isinstance(it["count"], int)

        # avg_response_time_ms: int o float
        assert isinstance(item["avg_response_time_ms"], (int, float)), "avg_response_time_ms debe ser numérico"

def test_stats_date_filtering(client_admin, seed_stats):
    """
    Si el endpoint acepta filtros ?from=YYYY-MM-DD&to=YYYY-MM-DD,
    valida que responda 200 y devuelva items (>=0).
    Si no implementa filtros, se omite.
    """
    day = seed_stats  # "YYYY-MM-DD"
    r = client_admin.get(STATS_ENDPOINT, params={"from": day, "to": day})
    if r.status_code in (400, 404, 405):
        pytest.skip("El endpoint no implementa filtros desde/hasta en este build.")
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"

    data = r.json()
    assert "items" in data and isinstance(data["items"], list)
    # Si hay ítems, al menos uno debe corresponder al día pedido
    if data["items"]:
        assert any((_is_yyyy_mm_dd(it.get("date", "")) and it["date"] == day) for it in data["items"]), \
            f"No se encontró item con date == {day}"
