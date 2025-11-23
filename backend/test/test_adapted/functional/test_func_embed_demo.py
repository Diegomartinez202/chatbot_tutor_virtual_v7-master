# backend/test/test_adapted/functional/test_func_embed_demo.py

from starlette.testclient import TestClient
from backend.main import app
from backend.config.settings import settings


client = TestClient(app)


def test_chat_embed_html_no_expuesto_en_backend():
    """
    Escenario:
      - Se intenta acceder a /chat-embed.html directamente contra el backend FastAPI.

    Diseño actual del proyecto:
      - El flujo EMBED híbrido se sirve desde el frontend (React/Vite) mediante
        hybrid-host.html y zajuna-bubble.js.
      - El backend ya NO expone /chat-embed.html como HTML propio (era un endpoint legacy).

    Criterio de aceptación:
      - El backend puede responder 404 (no implementado), sin error 500.
      - La evidencia de embed se valida en la capa frontend y en el informe técnico.
    """
    r = client.get("/chat-embed.html")
    # Aceptamos explícitamente que este endpoint ya no exista en FastAPI
    assert r.status_code == 404


def test_assets_basicos_redirigen_al_frontend_configurado():
    """
    Escenario:
      - Se solicitan assets básicos que, en modo embed/web, pueden ser servidos
        por el frontend (Vite / Nginx) y NO directamente por el backend.

    Diseño actual:
      - /favicon.ico: el backend redirige (302) hacia settings.frontend_site_url.
      - /bot-avatar.png y /android-chrome-192x192.png: pueden no estar
        configurados todavía y responder 404 en entorno local.

    Criterio de aceptación:
      - /favicon.ico:
          * Responde 301/302.
          * Location comienza con settings.frontend_site_url + "/".
      - Otros assets:
          * Pueden responder 301/302 hacia el frontend O 404 (no definido),
            pero nunca un 5xx.
    """
    frontend = settings.frontend_site_url.rstrip("/")
    local_client = TestClient(app)

    # 1) favicon.ico → DEBE redirigir al frontend
    r_fav = local_client.get("/favicon.ico", allow_redirects=False)
    assert r_fav.status_code in (301, 302), f"Estado inesperado para /favicon.ico: {r_fav.status_code}"
    loc_fav = r_fav.headers.get("location", "")
    assert loc_fav.startswith(f"{frontend}/"), (
        f"Location inesperado para /favicon.ico: {loc_fav} (esperado prefijo {frontend}/)"
    )

    # 2) Otros assets → aceptamos redirect o 404 (pero no 5xx)
    for path in ["/bot-avatar.png", "/android-chrome-192x192.png"]:
        r = local_client.get(path, allow_redirects=False)
        assert r.status_code in (301, 302, 404), f"Estado inesperado para {path}: {r.status_code}"
        if r.status_code in (301, 302):
            loc = r.headers.get("location", "")
            assert loc.startswith(f"{frontend}/"), (
                f"Location inesperado para {path}: {loc} (esperado prefijo {frontend}/)"
            )
