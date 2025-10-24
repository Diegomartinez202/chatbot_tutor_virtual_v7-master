# backend/main.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, RedirectResponse

# 🚀 Settings y logging unificado
from backend.utils.logging import setup_logging, get_logger
setup_logging()
log = get_logger(__name__)

from backend.config.settings import settings

# 🧩 Middlewares propios actualizados
from backend.middleware.request_id import RequestIdMiddleware
from backend.middleware.request_meta_middleware import request_meta_middleware
from backend.middleware.access_log_middleware import AccessLogMiddleware
from backend.middleware.auth_middleware import AuthMiddleware
# 🧭 Routers agregadores y controladores
from backend.routes import router as api_router
from backend.controllers import admin_controller as admin_ctrl
from backend.controllers import user_controller as users_ctrl

# ⏱️ Rate Limit opcional
from backend.ext.rate_limit import init_rate_limit
from backend.ext.redis_client import close_redis


# =========================================================
# 🚀 INICIALIZACIÓN DEL BACKEND - BANNER DEMO
# =========================================================
if getattr(settings, "demo_mode", False):
    print("\n" + "=" * 70)
    print("⚠️  MODO DEMO ACTIVADO")
    print("   El backend acepta el token simulado para pruebas.")
    print("=" * 70 + "\n")
else:
    print("✅ Modo producción: autenticación real activa.\n")

STATIC_DIR = Path(settings.static_dir).resolve()


def _parse_csv_or_space(v: str):
    s = (v or "").strip()
    if not s:
        return []
    if "," in s:
        return [x.strip() for x in s.split(",") if x.strip()]
    return [x.strip() for x in s.split() if x.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        debug=settings.debug,
        title="Zajuna Chat Backend",
        description="Backend para intents, autenticación, logs y estadísticas",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 🌐 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "allowed_origins_list", settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 🔎 Request-ID
    app.add_middleware(RequestIdMiddleware, header_name="X-Request-ID")

    # ➕ Middleware IP/UA
    app.middleware("http")(request_meta_middleware)

    # 🧾 Logging HTTP con duración, IP, user y request-id
    app.add_middleware(LoggingMiddleware)

    # 📜 Access logs a base de datos (usa request.state.user)
    app.add_middleware(AccessLogMiddleware)

    # 🔐 Auth: agrega request.state.user (JWT o demo)
    app.add_middleware(AuthMiddleware)

    # 📁 Archivos estáticos
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # 🔀 Rutas API principales
    app.include_router(api_router)
    app.include_router(admin_ctrl.router)
    app.include_router(users_ctrl.router)

    # 🔒 CSP (embebidos)
    @app.middleware("http")
    async def _csp_headers(request: Request, call_next):
        resp = await call_next(request)
        raw_env = os.getenv("EMBED_ALLOWED_ORIGINS", "")
        env_anc = _parse_csv_or_space(raw_env)
        ancestors = env_anc if env_anc else (settings.frame_ancestors or ["'self'"])
        resp.headers["Content-Security-Policy"] = f"frame-ancestors {' '.join(ancestors)};"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resp

    FRONT_BASE = (settings.frontend_site_url or "").rstrip("/")

    # ✅ Health check
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

    # Logs de arranque
    if settings.debug:
        log.warning("🛠️ MODO DEBUG ACTIVADO. No recomendado para producción.")
    else:
        log.info("🛡️ Modo producción activado.")

    if not settings.secret_key or len(settings.secret_key) < 32:
        log.warning('⚠️ SECRET_KEY débil. Genera una con: python -c "import secrets; print(secrets.token_urlsafe(64))"')

    log.info("🚀 FastAPI montado. Rutas listas.")
    return app


app = create_app()


# ─────────────────────────────────────────────────────
# FastAPI-Limiter opcional
# ─────────────────────────────────────────────────────
@app.on_event("startup")
async def _startup():
    provider = (os.getenv("RATE_LIMIT_PROVIDER", "builtin") or "builtin").lower().strip()
    if provider == "fastapi-limiter":
        await init_rate_limit(app)

@app.on_event("shutdown")
async def _shutdown():
    provider = (os.getenv("RATE_LIMIT_PROVIDER", "builtin") or "builtin").lower().strip()
    if provider == "fastapi-limiter":
        await close_redis()


# 🔥 Standalone
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)