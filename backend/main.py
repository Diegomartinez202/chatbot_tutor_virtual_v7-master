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

from typing import List, Optional  
from backend.auth.deps import get_current_user
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.models.user_model import (
    RolEnum,
    UserLogin,
    UserToken,
    UserResponse,
    UserOut,
    UserUpdate,
    Calificacion,
    CalificacionesResponse,
    EstadoUsuarioResponse,
    EstadoEstudianteResponse,
    Certificado,
    CertificadosResponse,
    Horario,
    HorariosResponse,
    CursoProgreso,
    ProgresoResponse,
    TutorResponse,
)

from backend.db.mongodb import (
    get_users_chat_collection,
    get_tutores_collection,
    get_progreso_cursos_collection,
    get_horarios_collection,
    get_certificados_collection,
    get_calificaciones_collection,
)

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
# ============================
#  MODELOS DE CERTIFICADOS
# ============================
class Certificado(BaseModel):
    curso: str
    fecha: str
    url: Optional[str] = None
    tipo: Optional[str] = "certificado"


class CertificadosResponse(BaseModel):
    certificados: List[Certificado]


# ============================
#  CALIFICACIONES POR USUARIO
# ============================
@app.get(
    "/api/usuarios/{user_id}/calificaciones",
    response_model=CalificacionesResponse,
)
def get_calificaciones(
    user_id: str,
    user: UserOut = Depends(get_current_user),
):
    """
    Devuelve las calificaciones del usuario desde MongoDB.
    - Estudiante: solo puede ver sus propias calificaciones.
    - Admin/soporte: pueden ver las de cualquier user_id.
    """
    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value in ("admin", "soporte"):
   
        pass
    elif role_value == "estudiante":
     
        if user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes ver las calificaciones de otro usuario.",
            )
    else:
    
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver calificaciones.",
        )

    col = get_calificaciones_collection()
    docs = list(col.find({"user_id": user_id}))

    calificaciones = [
        Calificacion(
            curso=doc.get("curso", "Curso"),
            nota=float(doc.get("nota", 0.0)),
        )
        for doc in docs
    ]

    return CalificacionesResponse(
        usuario=user_id,
        calificaciones=calificaciones,
    )

class TutorResponse(BaseModel):
    nombre: str
    contacto: str 

@app.get("/api/tutor", response_model=TutorResponse)
def get_tutor(user: UserOut = Depends(get_current_user)):
    
    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value not in ("admin", "soporte", "estudiante"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar tutor.",
        )

    col = get_tutores_collection()
    doc = col.find_one({"user_id": user.id})

    if not doc:
        return TutorResponse(
            nombre="Tutor no asignado",
            contacto="Sin contacto",
        )

    return TutorResponse(
        nombre=doc["nombre"],
        contacto=doc["contacto"]
    )

class Horario(BaseModel):
    curso: str
    dia: str
    hora: str
    aula: Optional[str] = None


class HorariosResponse(BaseModel):
    horarios: List[Horario]


@app.get("/api/horarios")
def get_horarios(user: UserOut = Depends(get_current_user)):
   
    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value not in ("admin", "soporte", "estudiante"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar horarios.",
        )

    col = get_horarios_collection()
    docs = list(col.find({"user_id": user.id}))

    horarios = [
        {
            "curso": doc.get("curso"),
            "dia": doc.get("dia"),
            "hora": doc.get("hora"),
            "aula": doc.get("aula"),
        }
        for doc in docs
    ]

    return HorariosResponse(horarios=horarios)

class CursoProgreso(BaseModel):
    nombre: str
    avance: Optional[int] = None  


class ProgresoResponse(BaseModel):
    avance_global: Optional[int] = None
    cursos: List[CursoProgreso] = Field(default_factory=list)


@app.get("/api/progreso-cursos")
def get_progreso_cursos(user: UserOut = Depends(get_current_user)):
   
    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value not in ("admin", "soporte", "estudiante"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar progreso de cursos.",
        )

    col = get_progreso_cursos_collection()
    docs = list(col.find({"user_id": user.id}))

    cursos = []
    total = 0
    count = 0

    for doc in docs:
        avance = doc.get("avance")
        if isinstance(avance, (int, float)):
            total += avance
            count += 1

        cursos.append({
            "nombre": doc.get("curso"),
            "avance": avance,
        })

    avance_global = int(total / count) if count else None

    return ProgresoResponse(
      avance_global=avance_global,
      cursos=[
          CursoProgreso(
              nombre=curso["nombre"],
              avance=curso["avance"],
          )
          for curso in cursos
        ]
    )

@app.get("/api/usuarios/{user_id}", response_model=UserOut)
def get_usuario(
    user_id: str,
    user: UserOut = Depends(get_current_user),
):
    """
    Devuelve los datos del usuario.
    - Estudiante: solo puede ver SUS propios datos.
    - Admin/soporte: puede consultar cualquier user_id.
    """

    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value in ("admin", "soporte"):
        
        pass
    elif role_value == "estudiante":
        
        if user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes ver los datos de otro usuario.",
            )
    else:
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver datos de usuario.",
        )

    col = get_users_chat_collection()
    doc = col.find_one({"_id": user_id}) or col.find_one({"id": user_id})

    if not doc:
       
        return UserOut(
            id=user_id,
            nombre="Estudiante Demo",
            email=user.email,
            rol=user.rol,
            documento="123456789",
            programa="Tecnólogo en Gestión Administrativa",
            estado="Activo",
        )

    raw_role = doc.get("rol") or role_value or "usuario"

    return UserOut(
        id=str(doc.get("_id") or doc.get("id") or user_id),
        nombre=doc.get("nombre", "Estudiante"),
        email=doc.get("email", user.email),
        rol=RolEnum(raw_role),
        documento=doc.get("documento"),
        programa=doc.get("programa"),
        estado=doc.get("estado", "Activo"),
    )

@app.get(
    "/api/usuarios/{user_id}/estado",
    response_model=EstadoUsuarioResponse,
)
def get_estado_por_usuario(
    user_id: str,
    user: UserOut = Depends(get_current_user),
):
    """
    Devuelve el estado académico del usuario.
    - Estudiante: solo puede ver su propio estado.
    - Admin/soporte: pueden consultar el estado de cualquier user_id.
    """

    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value in ("admin", "soporte"):
        pass
    elif role_value == "estudiante":
        if user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes ver el estado de otro usuario.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver estado académico.",
        )

    col = get_users_chat_collection()
    doc = col.find_one({"_id": user_id}) or col.find_one({"id": user_id})

    estado = (doc or {}).get("estado", "Activo")

    return EstadoUsuarioResponse(
        usuario=user_id,
        estado=estado,
    )

@app.get("/api/certificados", response_model=CertificadosResponse)
def get_certificados(user: UserOut = Depends(get_current_user)):
   
    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value not in ("admin", "soporte", "estudiante"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar certificados.",
        )

    col = get_certificados_collection()
    docs = list(col.find({"user_id": user.id}))

    if not docs:
        
        demo_data = [
            Certificado(
                curso="Excel Intermedio",
                fecha="2025-06-10",
                url="https://zajuna.edu/cert/123",
            ),
            Certificado(
                curso="Programación Básica",
                fecha="2025-04-02",
                url="https://zajuna.edu/cert/456",
            ),
        ]
        return CertificadosResponse(certificados=demo_data)

    certificados = []
    for d in docs:
        certificados.append(
            Certificado(
                curso=d.get("curso") or d.get("programa") or "Certificado",
                fecha=d.get("fecha") or d.get("fecha_emision") or "",
                url=d.get("url"),
                tipo=d.get("tipo", "certificado"),
            )
        )

    return CertificadosResponse(certificados=certificados)

class EstadoEstudianteResponse(BaseModel):
    estado: str  


@app.get("/api/estado-estudiante", response_model=EstadoEstudianteResponse)
def get_estado_estudiante(user: UserOut = Depends(get_current_user)):
   
    role_value = getattr(user, "rol", None)
    if hasattr(role_value, "value"):
        role_value = role_value.value

    if role_value not in ("admin", "soporte", "estudiante"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar estado de estudiante.",
        )

    col = get_users_chat_collection()
    doc = col.find_one({"_id": user.id})

    estado = doc.get("estado", "Activo") if doc else "Activo"

    return EstadoEstudianteResponse(estado=estado)

