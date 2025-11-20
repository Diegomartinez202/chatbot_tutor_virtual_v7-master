from __future__ import annotations  

from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, RedirectResponse, HTMLResponse

from backend.utils.logging import setup_logging, get_logger
setup_logging()
log = get_logger(__name__)  

from backend.config.settings import settings

from backend.middleware.request_id import RequestIdMiddleware
from backend.middleware.request_meta_middleware import request_meta_middleware
from backend.middleware.log_middleware import LoggingMiddleware
from backend.middleware.access_log_middleware import AccessLogMiddleware
from backend.middleware.auth_middleware import AuthMiddleware

from backend.routes import router as api_router
from backend.controllers import admin_controller as admin_ctrl
from backend.controllers import user_controller as users_ctrl

from backend.routes.me_settings import router as me_router                 
from backend.routes.user_settings import router as user_settings_router    
from backend.routes.chat import router as root_router, chat_router as chat_api_router

from backend.ext.rate_limit import init_rate_limit
from backend.ext.redis_client import close_redis

from backend.db.mongodb import get_database 

from backend.middleware.cors_csp import add_cors_and_csp
from backend.middleware.permissions_policy import add_permissions_policy
from pymongo import MongoClient

from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from starlette.middleware.base import BaseHTTPMiddleware
from backend.routes.chat_proxy import router as chat_proxy_router

# ─────────────────────────────────────────
# Modo demo / producción
# ─────────────────────────────────────────
if getattr(settings, "demo_mode", False):
    print("\n" + "=" * 70)
    print("⚠️  MODO DEMO ACTIVADO")
    print("   El backend acepta el token simulado para pruebas.")
    print("=" * 70 + "\n")
else:
    print("✅ Modo producción: autenticación real activa.\n")

STATIC_DIR = Path(settings.static_dir).resolve()

logger = log


def _parse_csv_or_space(v: str):
    s = (v or "").strip()
    if not s:
        return []
    if "," in s:
        return [x.strip() for x in s.split(",") if x.strip()]
    return [x.strip() for x in s.split() if x.strip()]


class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "   
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        response.headers["Content-Security-Policy"] = csp
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        debug=settings.debug,
        title="Zajuna Chat Backend",
        description="Backend para intents, autenticación, logs y estadísticas",
        version="2.0.0",
        docs_url=None,   # usamos /docs custom
        redoc_url=None,  # usamos /redoc custom
    )

    # Permissions-Policy
    app_env = (getattr(settings, "app_env", None) or os.getenv("APP_ENV") or "prod").lower()
    add_permissions_policy(app, preset="relaxed" if app_env == "dev" else "strict")
    add_permissions_policy(
        app,
        policy=getattr(settings, "permissions_policy_effective", None),
        add_legacy_feature_policy=True,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "allowed_origins_list", settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
 
    add_cors_and_csp(app)
    app.add_middleware(CSPMiddleware)

    # Middlewares varios
    app.add_middleware(RequestIdMiddleware, header_name="X-Request-ID")
    app.middleware("http")(request_meta_middleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(AuthMiddleware)

    # Static
    Path(STATIC_DIR).mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # ─────────────────────────────────────────
    # Agrupador /api
    # ─────────────────────────────────────────
    api = APIRouter()

    api.include_router(admin_ctrl.router)
    api.include_router(users_ctrl.router)
    api.include_router(chat_api_router)
    api.include_router(root_router)
    api.include_router(me_router)
    api.include_router(
        user_settings_router,
        prefix="/me",
        tags=["user-settings"],
    )
    app.include_router(api_router, prefix="/api")
    app.include_router(root_router, prefix="/api")
    app.include_router(chat_api_router, prefix="/api")
    app.include_router(chat_proxy_router, prefix="/api")
 
    app.include_router(api)

    # CSP adicional para frame-ancestors
    @app.middleware("http")
    async def _csp_headers(request: Request, call_next):
        resp = await call_next(request)
        if "Content-Security-Policy" not in resp.headers:
            raw_env = os.getenv("EMBED_ALLOWED_ORIGINS", "")
            env_anc = _parse_csv_or_space(raw_env)
            ancestors = env_anc if env_anc else (settings.frame_ancestors or ["'self'"])
            resp.headers["Content-Security-Policy"] = f"frame-ancestors {' '.join(ancestors)};"
            resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resp

    FRONT_BASE = (settings.frontend_site_url or "").rstrip("/")

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"ok": True}

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/favicon.ico", status_code=302)
        return Response(status_code=404)

    @app.get("/site.webmanifest", include_in_schema=False)
    async def manifest():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/site.webmanifest", status_code=302)
        data = {
            "name": "Chatbot Tutor Virtual",
            "short_name": "TutorBot",
            "description": "Asistente virtual para consultas y soporte.",
            "lang": "es",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "theme_color": "#0f172a",
            "background_color": "#ffffff",
            "icons": [
                {"src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"},
            ],
        }
        return JSONResponse(data, media_type="application/manifest+json")

    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "✅ API del Chatbot Tutor Virtual en funcionamiento"}

    if settings.debug:
        log.warning("🛠️ MODO DEBUG ACTIVADO. No recomendado para producción.")
    else:
        log.info("🛡️ Modo producción activado.")

    if not settings.secret_key or len(settings.secret_key) < 32:
        log.warning('⚠️ SECRET_KEY débil. Genera una con: python -c "import secrets; print(secrets.token_urlsafe(64))"')

    log.info("🚀 FastAPI montado. Rutas listas.")
    return app


# ---- Instanciamos la app ----
app = create_app()


@app.get("/debug-routes", include_in_schema=False)
def debug_routes():
    return [f"{route.path} -> {getattr(route, 'name', '')}" for route in app.routes]


# ---- Rutas de documentación Swagger/ReDoc fuera de create_app ----

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Swagger UI - Zajuna Chat Backend</title>
        <link rel="stylesheet" type="text/css" href="/static/swagger-ui.css" />
        <style>
          body { margin: 0; padding: 0; }
          #swagger-ui { box-sizing: border-box; }
        </style>
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="/static/swagger-ui-bundle.js"></script>
        <script src="/static/swagger-ui-standalone-preset.js"></script>
        <script>
        window.onload = function() {
          const ui = SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: "#swagger-ui",
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIStandalonePreset
            ],
            layout: "StandaloneLayout",
            docExpansion: "none",
            defaultModelsExpandDepth: -1
          });
          window.ui = ui;
        };
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_docs():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>ReDoc - Documentación Chatbot Tutor Virtual</title>
        <meta charset="utf-8" />
      </head>
      <body>
        <redoc spec-url="/openapi.json"></redoc>
        <script src="/static/redoc.standalone.js"></script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
