from __future__ import annotations

from fastapi.testclient import TestClient


DEFAULTS = {
    "language": "es",
    "theme": "light",
    "fontScale": 1.0,
    "highContrast": False,
}


def test_get_settings_defaults(client: TestClient):
    # Como no existe doc en user_settings, debe devolver defaults
    r = client.get("/api/me/settings", headers={"Authorization": "Bearer demo"})
    assert r.status_code == 200
    data = r.json()
    assert data == DEFAULTS


def test_put_then_get_settings_roundtrip(client: TestClient):
    # Actualizamos preferencias válidas
    payload = {
        "language": "en",
        "theme": "dark",
        "fontScale": 1.25,
        "highContrast": True,
    }
    r = client.put("/api/me/settings", json=payload, headers={"Authorization": "Bearer demo"})
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert j["prefs"]["language"] == "en"
    assert j["prefs"]["theme"] == "dark"
    assert j["prefs"]["fontScale"] == 1.25
    assert j["prefs"]["highContrast"] is True

    # GET debe reflejar lo guardado
    r2 = client.get("/api/me/settings", headers={"Authorization": "Bearer demo"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["language"] == "en"
    assert d2["theme"] == "dark"
    assert d2["fontScale"] == 1.25
    assert d2["highContrast"] is True


def test_put_normaliza_valores_fuera_de_rango(client: TestClient):
    # Enviamos valores fuera de rango/invalidos: el servicio los normaliza
    payload = {
        "language": "xx",       # -> "es"
        "theme": "nope",        # -> "light"
        "fontScale": 999,       # -> cap a 2.0
        "highContrast": 1,      # -> bool(True)
    }
    r = client.put("/api/me/settings", json=payload, headers={"Authorization": "Bearer demo"})
    assert r.status_code == 200
    j = r.json()
    prefs = j["prefs"]
    assert prefs["language"] == "es"
    assert prefs["theme"] == "light"
    assert prefs["fontScale"] == 2.0
    assert prefs["highContrast"] is True
