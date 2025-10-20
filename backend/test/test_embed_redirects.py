from starlette.testclient import TestClient
from backend.main import app

def test_chat_embed_redirect(monkeypatch):
    client = TestClient(app)
    # Asegura FRONTEND_SITE_URL para el test
    monkeypatch.setenv("FRONTEND_SITE_URL", "http://frontend.local")
    r = client.get("/chat-embed.html", allow_redirects=False)
    assert r.status_code in (301, 302)
    assert r.headers["location"].startswith("http://frontend.local/chat-embed.html")

def test_assets_redirect(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("FRONTEND_SITE_URL", "http://frontend.local")
    for path in ["/favicon.ico", "/bot-avatar.png", "/android-chrome-192x192.png"]:
        r = client.get(path, allow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"].startswith("http://frontend.local/")
