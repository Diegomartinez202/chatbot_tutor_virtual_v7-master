# backend/test_adapted/functional/test_func_embed_demo.py
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_chat_embed_html_modo_demo(monkeypatch):
    """
    Escenario: página de burbuja embebida.

    Caso 1: sin FRONTEND_SITE_URL → se espera que el backend sirva
    directamente el HTML de demo o similar (200).
    """
    monkeypatch.delenv("FRONTEND_SITE_URL", raising=False)
    r = client.get("/chat-embed.html", allow_redirects=False)

    assert r.status_code in (
        200,
        301,
        302,
    ), f"Estado inesperado para /chat-embed.html: {r.status_code}"


def test_chat_embed_redirige_a_frontend_si_hay_url(monkeypatch):
    """
    Escenario: se configura FRONTEND_SITE_URL (por ejemplo, página externa
    con el widget burbuja embebido).

    Debe redirigir a FRONTEND_SITE_URL/chat-embed.html sin hacer login real.
    """
    monkeypatch.setenv("FRONTEND_SITE_URL", "http://frontend.local")

    r = client.get("/chat-embed.html", allow_redirects=False)
    assert r.status_code in (301, 302)
    loc = r.headers.get("location", "")
    assert loc.startswith(
        "http://frontend.local"
    ), f"Location inesperado: {loc}"


def test_assets_basicos_redirigidos_al_frontend(monkeypatch):
    """
    Escenario: favicon y assets de la burbuja en modo embebido.

    Con FRONTEND_SITE_URL definido, los activos estáticos deben
    redirigirse a dicho frontend (propuesta embed híbrido).
    """
    monkeypatch.setenv("FRONTEND_SITE_URL", "http://frontend.local")
    client_local = TestClient(app)

    for path in ["/favicon.ico", "/bot-avatar.png", "/android-chrome-192x192.png"]:
        r = client_local.get(path, allow_redirects=False)
        assert r.status_code in (301, 302)
        assert r.headers.get("location", "").startswith("http://frontend.local/")
