🐍 Backend FastAPI — Chatbot Tutor Virtual

Backend de administración y orquestación para el Chatbot Tutor Virtual.
Expone APIs para chat, intents, usuarios, tickets/helpdesk, logs y estadísticas; integra con Rasa y Action Server.

✅ Este documento no modifica tu lógica de negocio. Es guía operativa (DEV/PROD), variables de entorno, rate-limit y CI/CD.

⚙️ Arquitectura (resumen)

FastAPI con middlewares de Request-ID, logging, access log, auth y CSP.

Rutas montadas en:

/api/* (APIs principales; admin legacy y v2 conviven)

/chat/* y espejo /api/chat/* (compatibilidad UI)

Rasa (NLP/NLU) y Action Server vía HTTP:

RASA_URL (p. ej. http://rasa:5005)

ACTION_SERVER_URL está en el contenedor Rasa (apunta al action-server)

MongoDB como base de datos (intents, logs, usuarios, etc.).

Rate limiting con 3 proveedores (feature flag por ENV):

builtin (memoria o Redis) — recomendado por defecto

slowapi (si instalas dependencias)

fastapi-limiter (si ya lo usas)

🗂️ Estructura relevante
backend/
├─ config/
│  └─ settings.py          # Config central (CORS, Mongo, Redis, flags, etc.)
├─ middleware/
│  ├─ request_id.py
│  ├─ access_log_middleware.py
│  ├─ logging_middleware.py
│  └─ auth_middleware.py
├─ routes/
│  ├─ __init__.py          # api_router
│  ├─ chat.py              # /chat y /api/chat
│  ├─ api_chat.py          # compat
│  ├─ helpdesk.py          # tickets desde Action Server
│  ├─ admin_auth.py        # /api/admin2 (mejoras)
│  ├─ admin_users.py       # /api/admin/users
│  ├─ auth_admin.py        # /api/admin (legacy)
│  ├─ intent_controller.py # moderno
│  ├─ intent_legacy_controller.py
│  ├─ stats.py
│  ├─ logs.py  / logs_v2.py
│  └─ exportaciones.py
├─ services/               # process_user_message, jwt_service, etc.
├─ db/                     # mongodb helpers
├─ utils/                  # logging helpers
├─ ext/
│  ├─ rate_limit.py        # integración opcional (decoradores/helpers)
│  └─ redis_client.py
├─ main.py                 # crea la app, CORS, CSP, routers y rate-limit
└─ requirements.txt

✅ Endpoints clave (smoke)

Health / Docs

GET / → { "message": "✅ API del Chatbot Tutor Virtual en funcionamiento" }

GET /health → { "ok": true }

GET /api/docs → Swagger UI

Chat

GET /chat/health y /api/chat/health

POST /chat y /api/chat → envía mensaje del usuario (rate-limited)

Logs/Stats: /api/... (según routers)

Admin / Usuarios: /api/admin (legacy) y /api/admin2, /api/admin/users (v2)

🔐 Rate-limit (activable por ENV, sin tocar código)

Tu main.py ya soporta 3 proveedores. Actívalo solo con variables:

A) Builtin (memoria) — simple
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=builtin
RATE_LIMIT_BACKEND=memory
# Política por defecto (si está soportada en settings):
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SEC=60

B) Builtin (Redis) — recomendado para prod
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=builtin
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis:6379/0

C) SlowAPI (si instalas dependencias)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=slowapi
RATE_LIMIT_STORAGE_URI=redis://redis:6379/0


Requiere en requirements.txt: slowapi>=0.1.9 y redis>=5.0.

Política activa por defecto: 60 req/min en POST /chat y /api/chat.
Con SlowAPI se expone además GET /api/_rate_test para probar la cuota.

🌍 CORS, CSP y seguridad

CORS desde settings.allowed_origins_list. En dev ya permite http://localhost:5173.

CSP (frame-ancestors) configurable con EMBED_ALLOWED_ORIGINS (espacios/comas) o settings.frame_ancestors.

Headers de seguridad adicionales también por el reverse proxy Nginx (prod).

🔧 Variables de entorno del backend

Crea backend/.env (dev) y backend/.env.production (prod). Ejemplo base:

# === Core ===
APP_ENV=dev
DEBUG=true
SECRET_KEY=change_me_long_random_string

# Base de datos
MONGO_URI=mongodb://mongo:27017/chatbot_tutor_virtual_v2

# Rasa base URL (HTTP)
RASA_URL=http://rasa:5005

# Frontend público (para redirecciones de assets)
FRONTEND_SITE_URL=http://localhost:5173/

# CORS (lista separada por comas)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost

# CSP (frame-ancestors) — lista (espacios o comas)
EMBED_ALLOWED_ORIGINS='self' http://localhost http://localhost:5173

# === Rate limit ===
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=builtin       # builtin | slowapi | fastapi-limiter
RATE_LIMIT_BACKEND=memory         # memory | redis (para builtin)
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SEC=60

# Logging
LOG_LEVEL=INFO


Prod: DEBUG=false, APP_ENV=prod y genera SECRET_KEY fuerte:
python -c "import secrets; print(secrets.token_urlsafe(64))"

▶️ Arranque (tres formas)
1) Todo con Docker (perfil build)

Pruebas integradas con Vite (HMR), Rasa y Actions.

# desde la raíz del repo
docker compose --profile build up -d mongo action-server rasa backend-dev admin-dev nginx-dev
docker compose --profile build logs -f backend-dev rasa action-server
# UI: http://localhost/  (nginx-dev proxifica admin-dev:5173)
# API docs: http://localhost:8000/docs

2) Producción local (perfil prod)
docker compose --profile prod build
docker compose --profile prod up -d
# UI: http://localhost/
# API: http://localhost/api
# Rasa: http://localhost/rasa  (WS: ws://localhost/ws)

3) Híbrido: Backend local (venv) + Rasa/Actions/Mongo en Docker

Útil para depurar en Windows con Python 3.12 (tu caso actual).

# 3.1 Dependencias en Docker
docker compose --profile build up -d mongo action-server rasa

# 3.2 Backend local con venv (Visual Studio 2022 / PowerShell)
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# Docs: http://127.0.0.1:8000/docs


En Linux/Mac: python3.12 -m venv .venv && source .venv/bin/activate.

🧪 Smoke rápido

FastAPI: GET http://127.0.0.1:8000/chat/health → {"ok": true}

Rasa: GET http://127.0.0.1:5005/status

Action Server: GET http://127.0.0.1:5055/health

Chat (PowerShell):

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -Body (@{
  sender="qa-session"
  message="hola"
} | ConvertTo-Json) -ContentType "application/json"

🔌 Integración con Rasa

El backend envía a Rasa propagando metadata (incluye auth.hasToken y claims si hay JWT).

URL base: RASA_URL (p. ej. http://rasa:5005).

Rutas útiles de Rasa: /webhooks/rest/webhook, /model/parse, /status.

📝 Logs

Cada request tiene X-Request-ID (middleware).

logs_v2 y logs legacy coexisten (compatibilidad).

Se registra latencia hacia Rasa (latency_ms) en Mongo (best-effort).

🛡️ Auth-gating (comportamiento del bot)

Sin token (metadata.auth.hasToken=false): intents protegidos responden con utter_need_auth.

Con token válido (JWT): el bot habilita intents privados (p. ej., estado estudiante / certificados).

El backend inspecciona Authorization: Bearer <token> y agrega claims a metadata.

🧰 Scripts útiles (raíz del repo)

check_health.ps1: verifica FastAPI, Rasa y Action Server; abre /docs si todo OK.

scripts/tasks.ps1: atajos one-click (start/stop/logs/health) para build y prod.

Ejemplos:

# DEV/BUILD
.\scripts\tasks.ps1 -Profile build -Rebuild

# PROD
.\scripts\tasks.ps1 -Profile prod -Rebuild

🧑‍💻 Visual Studio 2022 (Windows)

Abrir carpeta del repo en VS2022 (File > Open > Folder…).

Terminal integrada (PowerShell): View > Terminal.

Backend local con venv 3.12:

cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000


Servicios Docker (Rasa/Actions/Mongo) desde la terminal en la raíz:

docker compose --profile build up -d mongo action-server rasa


Probar:

API docs: http://127.0.0.1:8000/docs

Rasa: http://127.0.0.1:5005/status

Actions: http://127.0.0.1:5055/health

Si prefieres todo Docker: usa .\scripts\tasks.ps1 -Profile build -Rebuild.

🛠️ Troubleshooting

429 inesperado: sube RATE_LIMIT_MAX_REQUESTS/RATE_LIMIT_WINDOW_SEC, o usa RATE_LIMIT_BACKEND=memory.

CORS en dev: ALLOWED_ORIGINS debe incluir http://localhost:5173.

Mongo no conecta: revisa MONGO_URI y que mongo esté healthy.

Rasa/Actions 404: valida RASA_URL y que Rasa apunte a ACTION_SERVER_URL correcto.

WebSocket en prod: usa wss:// detrás de TLS y verifica mapeo Nginx /ws.

Puertos ocupados: libera 80/443/8000/5005/5055/5173/6379.

🚀 CI/CD (pistas rápidas)

Build backend (si tienes Dockerfile multistage):

docker build -t org/backend:latest ./backend
docker push org/backend:latest


Compose prod:

docker compose --profile prod build
docker compose --profile prod up -d

📎 Enlaces cruzados

Guía global: ../README-deploy.md

Frontend (Vite/React): ../admin_panel_react/README.md

Rasa (bot + endpoints): ../rasa/README.md

Docker ops: ../docs/DOCKER.md