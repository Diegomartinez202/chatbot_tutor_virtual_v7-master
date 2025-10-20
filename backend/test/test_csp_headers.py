from starlette.testclient import TestClient
from backend.main import app

def test_csp_headers(monkeypatch):
    monkeypatch.setenv("EMBED_ALLOWED_ORIGINS", "'self' http://localhost:5173")
    client = TestClient(app)
    r = client.get("/health")
    csp = r.headers.get("content-security-policy", "")
    assert "frame-ancestors" in csp
    assert "http://localhost:5173" in csp
