# backend/main.py
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from typing import Deque, DefaultDict, Any, Dict
from time import time
from collections import defaultdict, deque
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, RedirectResponse

# 🚀 Settings y logging unificado
from backend.utils.logging import setup_logging, get_logger
setup_logging()

from backend.config.settings import settings
from backend.middleware.request_id import RequestIdMiddleware

# 🧩 Middlewares propios
from backend.middleware.auth_middleware import AuthMiddleware
# -- IMPORT SEGURO (opcional) para evitar fallos si falta el archivo:
try:
    from backend.middleware.logging_middleware import LoggingMiddleware
    _LOGGING_MIDDLEWARE_AVAILABLE = True
except Exception:
    _LOGGING_MIDDLEWARE_AVAILABLE = False
    LoggingMiddleware = None  # type: ignore

from backend.middleware.access_log_middleware import AccessLogMiddleware
from backend.middleware.request_meta import request_meta_middleware  # IP/UA

# 🧭 Router agregador central (incluye auth_routes, auth_tokens, chat, logs, etc.)
from backend.routes import router as api_router

# 🧭 Routers adicionales/legacy que NO están todos en el agregador (se mantienen)
from backend.routes import exportaciones
from app.routers import admin_failed
from backend.routes import helpdesk
from backend.routes import api_chat
from app.routes.media import router as media_router
from backend.routes import auth_admin          # /api/admin (legacy)
from backend.routes import admin_auth          # /api/admin2 (mejoras auth)
from backend.routes import admin_users         # /api/admin/users (gestión usuarios)
from backend.routes import intent_legacy_controller
from backend.routes import logs as logs_legacy  # legacy
from backend.routes import logs_v2
from backend.routes.chat import chat_router  # /chat, /chat/health, /chat/debug
from app.routers import chat_audio
from backend.routes.admin_auth import router as admin_v2_router
from backend.routes.auth_admin import router as admin_legacy_router
# ✅ Montaje adicional directo de tokens para compat (/auth/* además de /api/auth/*)
from backend.routes.auth_tokens import router as auth_tokens_router

# ✅ Rutas extra que pediste mantener
from backend.routes import auth, admin

# Publica el limiter para decoradores @limit(...) sin imports circulares
from backend.rate_limit import set_limiter  # el helper es tolerante si no hay SlowAPI

# =========================================================
# 🚀 INICIALIZACIÓN DEL BACKEND - MODO DEMO
# =========================================================
# (Se mantiene el banner informativo)
from backend.config.settings import settings as _settings_dup_ref  # mantener compat si otro módulo lo usa

if getattr(settings, "demo_mode", False):
    print("\n" + "=" * 70)
    print("⚠️  MODO DEMO ACTIVADO")
    print("   El backend está aceptando el token simulado de Zajuna.")
    print("   Usa el siguiente header en tus pruebas de autenticación:")
    print("   Authorization: Bearer FAKE_TOKEN_ZAJUNA")
    print("=" * 70 + "\n")
else:
    print("✅ Modo producción: autenticación real activa.\n")

# Redis opcional (para rate-limit builtin en producción)
try:
    import redis.asyncio as aioredis  # pip install "redis>=5"
except Exception:
    aioredis = None

# (Opcional) SlowAPI para rate limiting por endpoint
try:
    from slowapi import Limiter  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore
    from slowapi.middleware import SlowAPIMiddleware  # type: ignore
    _SLOWAPI_OK = True
except Exception:
    _SLOWAPI_OK = False

# Proveedor de rate limit por ENV (extiendo con fastapi-limiter)
_PROVIDER = (os.getenv("RATE_LIMIT_PROVIDER", "builtin") or "builtin").lower().strip()
USE_SLOWAPI = (_PROVIDER == "slowapi")
USE_FASTAPI_LIMITER = (_PROVIDER == "fastapi-limiter")

STATIC_DIR = Path(settings.static_dir).resolve()
log = get_logger(__name__)


def _parse_csv_or_space(v: str):
    """Convierte 'a,b' o 'a b' → ['a','b'] (limpiando vacíos)."""
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
        description="Backend para gestión de intents, autenticación, logs y estadísticas del Chatbot Tutor Virtual",
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

    # 📁 Estáticos
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # 🔀 Rutas API principales vía agregador
    app.include_router(api_router, prefix="/api")

    # 🔀 Rutas adicionales/legacy
    app.include_router(admin_failed.router)
    app.include_router(exportaciones.router)
    app.include_router(helpdesk.router)
    app.include_router(api_chat.router)
    app.include_router(media_router)
    app.include_router(logs_legacy.router)
    app.include_router(logs_v2.router)
    app.include_router(admin_v2_router)
    app.include_router(admin_legacy_router)
    app.include_router(auth_tokens_router)
    app.include_router(intent_legacy_controller.router, prefix="/api/legacy", tags=["intents-legacy"])
    app.include_router(auth_admin.router)
    app.include_router(admin_auth.router)
    app.include_router(admin_users.router)
    app.include_router(chat_router)
    app.include_router(chat_router, prefix="/api")
    app.include_router(chat_audio.router)
    app.include_router(auth.router)
    app.include_router(admin.router)

    # 🔒 CSP (embebidos)
    @app.middleware("http")
    async def _csp_headers(request: Request, call_next):
        resp: Response = await call_next(request)
        raw_env = os.getenv("EMBED_ALLOWED_ORIGINS", "")
        env_anc = _parse_csv_or_space(raw_env)
        ancestors = env_anc if env_anc else (settings.frame_ancestors or ["'self'"])
        resp.headers["Content-Security-Policy"] = f"frame-ancestors {' '.join(ancestors)};"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resp

    # 🧠 Middlewares personalizados
    app.add_middleware(AccessLogMiddleware)
    if _LOGGING_MIDDLEWARE_AVAILABLE and LoggingMiddleware:
        app.add_middleware(LoggingMiddleware)
    else:
        print("[WARN] LoggingMiddleware no disponible; continuando sin él.")
    app.add_middleware(AuthMiddleware)

    # 🌐 Base pública frontend
    FRONT_BASE = (settings.frontend_site_url or "").rstrip("/")

    # ─────────────────────────────────────────────────────────────
    # Rate limiting: SlowAPI (opcional) / FastAPI-Limiter (opcional) / builtin
    # ─────────────────────────────────────────────────────────────
    if settings.rate_limit_enabled and USE_SLOWAPI and _SLOWAPI_OK and not getattr(app.state, "limiter", None):
        try:
            # Estrategia de clave configurable
            key_strategy = (getattr(settings, "rate_limit_key_strategy", "user_or_ip") or "user_or_ip").lower().strip()
            if key_strategy not in {"user_or_ip", "skip_admin", "ip"}:
                key_strategy = "user_or_ip"

            def key_user_or_ip(request) -> str:
                """Híbrida: JWT.sub si existe, si no, IP."""
                try:
                    claims: Dict[str, Any] = {}
                    if hasattr(request.state, "auth") and isinstance(getattr(request.state, "auth"), dict):
                        claims = request.state.auth.get("claims") or {}
                    uid = claims.get("sub")
                    if uid:
                        return f"user:{uid}"
                except Exception:
                    pass
                return f"ip:{get_remote_address(request)}"

            def key_skip_admin(request) -> str:
                """Exime admin (rol == 'admin'); resto como híbrida."""
                try:
                    claims: Dict[str, Any] = {}
                    if hasattr(request.state, "auth") and isinstance(getattr(request.state, "auth"), dict):
                        claims = request.state.auth.get("claims") or {}
                    if claims.get("rol") == "admin":
                        return f"bypass:{get_remote_address(request)}"
                    uid = claims.get("sub")
                    if uid:
                        return f"user:{uid}"
                except Exception:
                    pass
                return f"ip:{get_remote_address(request)}"

            key_func = {
                "user_or_ip": key_user_or_ip,
                "skip_admin": key_skip_admin,
                "ip": lambda request: f"ip:{get_remote_address(request)}",
            }[key_strategy]

            storage_uri = settings.rate_limit_storage_uri_effective  # soporta RATE_LIMIT_STORAGE_URI o REDIS_URL
            limiter = Limiter(key_func=key_func, storage_uri=storage_uri)
            app.state.limiter = limiter
            app.add_middleware(SlowAPIMiddleware)

            # Handler 429 JSON (limpio y estable)
            @app.exception_handler(RateLimitExceeded)
            async def _slowapi_handler(request: Request, exc: RateLimitExceeded):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too Many Requests", "policy": str(exc)},
                )

            # Publica el limiter para decoradores @limit(...) en routers
            set_limiter(limiter)

            # Endpoint de prueba no invasivo (opcional)
            burst = max(1, int(settings.rate_limit_max_requests))
            window = max(1, int(settings.rate_limit_window_sec))

            @app.get("/api/_rate_test")
            @limiter.limit(f"{burst}/{window} seconds")
            def _rate_test():
                return {"ok": True, "provider": "slowapi"}

            log.info(f"RateLimit: SlowAPI activo (strategy={key_strategy}, storage={storage_uri}).")

        except Exception as e:
            log.error(f"SlowAPI no disponible ({e}). Se usará builtin.")
            _activate_builtin_rate_limit(app)

    elif settings.rate_limit_enabled and USE_FASTAPI_LIMITER:
        # La inicialización real se hace en el hook de startup (más abajo).
        log.info("RateLimit: FastAPI-Limiter seleccionado (init en startup).")
        # No activamos builtin aquí para evitar duplicidad.
    else:
        # Default o cualquier otro valor → builtin
        _activate_builtin_rate_limit(app)

    # =========================================================
    # ✅ Health y utilidades públicas (ONE TRUE HEALTH)
    # =========================================================
    @app.get("/health", include_in_schema=False)
    async def health():
        return {"ok": True}

    # 🔁 Redirects de assets al frontend
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/favicon.ico", status_code=302)
        return Response(status_code=404)

    @app.get("/apple-touch-icon.png", include_in_schema=False)
    async def apple_touch():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/apple-touch-icon.png", status_code=302)
        return Response(status_code=404)

    @app.get("/android-chrome-192x192.png", include_in_schema=False)
    async def android_192():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/android-chrome-192x192.png", status_code=302)
        return Response(status_code=404)

    @app.get("/android-chrome-512x512.png", include_in_schema=False)
    async def android_512():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/android-chrome-512x512.png", status_code=302)
        return Response(status_code=404)

    @app.get("/bot-avatar.png", include_in_schema=False)
    async def bot_avatar():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/bot-avatar.png", status_code=302)
        return Response(status_code=404)

    @app.get("/bot-loading.png", include_in_schema=False)
    async def bot_loading():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/bot-loading.png", status_code=302)
        return Response(status_code=404)

    # ✅ Startup: índices de admin v2 (no interfiere con legacy)
    @app.on_event("startup")
    async def _ensure_admin2_idx():
        try:
            await admin_auth.ensure_admin_indexes()
        except Exception as e:
            log.error(f"No se pudo asegurar índice de usuarios (v2): {e}")

    # 📄 Manifest → frontend o fallback
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
                {"src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                {"src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            ],
        }
        return JSONResponse(data, media_type="application/manifest+json")

    # Legacy → frontend
    @app.get("/chat-embed.html", include_in_schema=False)
    async def chat_embed_alias():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/chat-embed.html", status_code=302)
        return JSONResponse({"detail": "chat-embed vive en el frontend"}, status_code=501)

    @app.get("/widget.html", include_in_schema=False)
    async def legacy_widget_alias():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/chat-embed.html", status_code=301)
        return JSONResponse({"detail": "chat-embed vive en el frontend."}, status_code=501)

    @app.get("/static/widgets/widget.html", include_in_schema=False)
    async def legacy_static_widget_html():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/chat-embed.html", status_code=301)
        return JSONResponse({"detail": "chat-embed vive en el frontend."}, status_code=501)

    @app.get("/embedded.js", include_in_schema=False)
    async def legacy_embedded_js_alias():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/chat-widget.js", status_code=301)
        return JSONResponse({"detail": "chat-widget vive en el frontend."}, status_code=501)

    @app.get("/static/widgets/embed.js", include_in_schema=False)
    async def legacy_static_embed_js():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/chat-widget.js", status_code=301)
        return JSONResponse({"detail": "chat-widget vive en el frontend."}, status_code=501)

    @app.get("/static/widgets/embedded.js", include_in_schema=False)
    async def legacy_static_embedded_js():
        if FRONT_BASE:
            return RedirectResponse(url=f"{FRONT_BASE}/chat-widget.js", status_code=301)
        return JSONResponse({"detail": "chat-widget vive en el frontend."}, status_code=501)

    # 🌱 Root
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "✅ API del Chatbot Tutor Virtual en funcionamiento"}

    # Logs de arranque
    if settings.debug:
        log.warning("🛠️ MODO DEBUG ACTIVADO. No recomendado para producción.")
    else:
        log.info("🛡️ Modo producción activado.")

    if not settings.secret_key or len(settings.secret_key) < 32:
        log.warning('⚠️ SECRET_KEY es débil o inexistente. Genera una con: python -c "import secrets; print(secrets.token_urlsafe(64))"')

    log.info("🚀 FastAPI montado correctamente. Rutas en /api, /chat, /api/admin y /api/admin2")
    return app


def _activate_builtin_rate_limit(app: FastAPI) -> None:
    """
    Rate-limit builtin (memoria/Redis) aplicado solo a POST /chat y /api/chat.
    Conserva tu lógica original y está protegido contra doble registro.
    """
    if not settings.rate_limit_enabled:
        return

    # Evitar doble registro si ya existe el middleware
    if any(getattr(m, "name", "") == "builtin_rate_limit" for m in getattr(app, "user_middleware", [])):
        return

    _RATE_BUCKETS: DefaultDict[str, Deque[float]] = defaultdict(deque)
    redis_client = None

    @app.on_event("startup")
    async def _init_rate_limiter():
        nonlocal redis_client
        if settings.app_env == "test":
            object.__setattr__(settings, "rate_limit_enabled", False)
        if not settings.rate_limit_enabled:
            return
        if getattr(settings, "rate_limit_backend", "memory") == "redis":
            if aioredis is None or not settings.redis_url:
                object.__setattr__(settings, "rate_limit_backend", "memory")
                log.error("RateLimit: Redis no disponible o sin REDIS_URL. Usando 'memory'.")
                return
            try:
                redis_client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
                await redis_client.ping()
                log.info("RateLimit: backend Redis OK (builtin).")
            except Exception as e:
                log.error(f"RateLimit Redis error: {e}. Fallback 'memory'.")
                object.__setattr__(settings, "rate_limit_backend", "memory")

    @app.on_event("shutdown")
    async def _close_rate_limiter():
        nonlocal redis_client
        if redis_client:
            try:
                await redis_client.aclose()
            except Exception:
                pass

    @app.middleware("http", name="builtin_rate_limit")
    async def builtin_rate_limit(request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        is_chat_post = request.method == "POST" and (path == "/chat" or path == "/api/chat")
        if not is_chat_post:
            return await call_next(request)

        ip = getattr(request.state, "ip", None) or (request.client.host if request.client else "unknown")
        now = time()
        window = settings.rate_limit_window_sec
        max_req = settings.rate_limit_max_requests

        # Redis
        if getattr(settings, "rate_limit_backend", "memory") == "redis" and redis_client:
            key = f"rl:{ip}"
            try:
                async with redis_client.pipeline(transaction=True) as pipe:
                    pipe.incr(key)
                    pipe.expire(key, window)
                    count, _ = await pipe.execute()
                if int(count) > max_req:
                    return JSONResponse({"detail": "Rate limit exceeded. Intenta nuevamente en un momento."}, status_code=429)
                return await call_next(request)
            except Exception as e:
                log.error(f"RateLimit Redis error: {e}. Fallback 'memory'.")
                object.__setattr__(settings, "rate_limit_backend", "memory")

        # Memoria
        dq = _RATE_BUCKETS[ip]
        while dq and (now - dq[0]) > window:
            dq.popleft()
        if len(dq) >= max_req:
            return JSONResponse({"detail": "Rate limit exceeded. Intenta nuevamente en un momento."}, status_code=429)
        dq.append(now)
        return await call_next(request)


# Instancia de la app
app = create_app()

# 🔥 Standalone (dev)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)


# ─────────────────────────────────────────────────────────────
# FastAPI-Limiter (opcional) — SOLO si RATE_LIMIT_PROVIDER=fastapi-limiter
# ─────────────────────────────────────────────────────────────
from backend.ext.rate_limit import init_rate_limit
from backend.ext.redis_client import close_redis

@app.on_event("startup")
async def _startup():
    provider = (os.getenv("RATE_LIMIT_PROVIDER", "builtin") or "builtin").lower().strip()
    if provider == "fastapi-limiter":
        await init_rate_limit(app)   # si Redis no está disponible, no hace nada

@app.on_event("shutdown")
async def _shutdown():
    provider = (os.getenv("RATE_LIMIT_PROVIDER", "builtin") or "builtin").lower().strip()
    if provider == "fastapi-limiter":
        await close_redis()