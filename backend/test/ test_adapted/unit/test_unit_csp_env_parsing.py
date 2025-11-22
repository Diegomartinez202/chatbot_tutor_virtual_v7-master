# backend/test_adapted/unit/test_unit_csp_env_parsing.py
from starlette.testclient import TestClient
from backend.main import app


def test_csp_incluye_frame_ancestors_y_embed(monkeypatch):
    """
    Prueba semi-unitaria: verifica que al configurar EMBED_ALLOWED_ORIGINS
    la cabecera Content-Security-Policy incluya frame-ancestors con esas URLs.

    No requiere Zajuna ni panel admin.
    """
    monkeypatch.setenv("EMBED_ALLOWED_ORIGINS", "'self' http://localhost:5173")
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200

    csp = r.headers.get("content-security-policy", "")
    assert "frame-ancestors" in csp.lower()
    assert "http://localhost:5173" in csp
