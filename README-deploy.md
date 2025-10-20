🚀 Chatbot Tutor Virtual – Despliegue (DEV/PROD) con Docker

Stack: FastAPI (backend) + Rasa + Action Server + React/Vite (admin) + Nginx + Mongo (+ Redis opcional).
Este documento no cambia la lógica de negocio: explica cómo ejecutar y operar el proyecto.

📚 Índice

Perfiles de ejecución

Estructura del repo

Prerrequisitos

Comandos rápidos

Health / Endpoints clave

Rate limit (por variables)

Proxy Nginx y variantes sin proxy

Entornos locales (.venv) – Backend / Rasa / React

QA / Smoke tests

Troubleshooting

Documentos locales (más guías)

🧩 Perfiles de ejecución

build (DEV/testing): mongo, action-server, rasa, backend-dev (hot reload), admin-dev (Vite HMR), nginx-dev (proxy).

prod (entrega): mongo, action-server, rasa, backend (Uvicorn prod), admin (Nginx estático), nginx (reverse proxy).

vanilla (diagnóstico): imágenes oficiales montando carpetas (útil para aislar problemas; no para entrega).

Rutas en prod (tras el proxy):

/ → Admin (SPA)

/api → FastAPI

/rasa y /ws → Rasa HTTP/WS

🗂️ Estructura del repo
.
├─ backend/                      # FastAPI (tu lógica)
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ .env / .env.production
│  └─ main.py
├─ rasa/                         # Bot Rasa
│  ├─ Dockerfile
│  ├─ entrypoint.sh              # render endpoints + auto-train (opcional)
│  ├─ endpoints.tpl.yml          # default (Action Server)
│  ├─ endpoints.mongo.tpl.yml    # tracker en Mongo
│  └─ actions/                   # (si corres Rasa local)
├─ rasa_action_server/           # Dockerfile del Action Server
│  └─ requirements.txt           # (opcional)
├─ admin_panel_react/            # Panel (Vite/React + Nginx en prod)
│  ├─ Dockerfile
│  ├─ nginx.conf
│  ├─ .env.development
│  ├─ .env.production
│  ├─ .env.production.external   # variante “sin proxy”
│  └─ README.md
├─ ops/nginx/conf.d/
│  └─ app.conf                   # reverse proxy: /, /api, /rasa, /ws
├─ scripts/
│  ├─ tasks.ps1                  # start/stop/logs/health (one-click)
│  └─ make_venvs.ps1             # crea venvs locales (backend / rasa)
├─ docs/
│  └─ WINDOWS-QUICKSTART.md      # 👉 Guía paso a paso Windows/VS2022
├─ check_health.ps1
└─ docker-compose.yml

✅ Prerrequisitos

Docker Desktop 4.x (o Docker Engine + Compose v2)

PowerShell (Windows) o Bash (Linux/Mac)

Puertos libres: 80, 443, 8000, 5005, 5055, 5173, 6379

(Opcional) Python 3.12 y/o Python 3.11 si vas a correr backend/Rasa fuera de Docker

▶️ Comandos rápidos
DEV (perfil build)
# desde la raíz del repo
docker compose --profile build up -d mongo action-server rasa backend-dev admin-dev nginx-dev
docker compose --profile build logs -f backend-dev rasa action-server
# UI (proxy dev):       http://localhost/
# FastAPI docs direct:  http://localhost:8000/docs
# Rasa status direct:   http://localhost:5005/status
# Actions health:       http://localhost:5055/health

PROD (perfil prod)
docker compose --profile prod build
docker compose --profile prod up -d
docker compose --profile prod logs -f nginx backend rasa action-server
# UI (proxy prod):  http://localhost/
# API:              http://localhost/api
# Rasa:             http://localhost/rasa
# WS:               ws://localhost/ws

Atajo “one-click”
# Build/DEV
.\scripts\tasks.ps1 -Profile build -Rebuild

# PROD
.\scripts\tasks.ps1 -Profile prod -Rebuild

🩺 Health / Endpoints clave
FastAPI

GET / → {"message":"✅ API del Chatbot Tutor Virtual en funcionamiento"}

GET /health → {"ok": true}

GET /api/docs → Swagger UI

Chat

GET /chat/health y /api/chat/health

POST /chat y /api/chat (rate-limited)

Rasa

GET /status (o vía proxy: /rasa/status)

Action Server

GET /health (puerto 5055)

Script Windows (PowerShell)
.\check_health.ps1 -FastApiUrl http://127.0.0.1:8000 -RasaUrl http://127.0.0.1:5005 -ActionsUrl http://127.0.0.1:5055
# (si quieres validar a través del proxy)
# .\check_health.ps1 -FastApiUrl http://127.0.0.1/api -RasaUrl http://127.0.0.1/rasa -ActionsUrl http://127.0.0.1:5055

⏱️ Rate limit (por variables)

Ya viene integrado en backend/main.py. No toques código, solo ENV:

A) Builtin (memoria)

RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=builtin
RATE_LIMIT_BACKEND=memory


B) Builtin + Redis (recomendado)

RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=builtin
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis:6379/0


Asegura el servicio redis y el volumen redis-data en docker-compose.yml.

C) SlowAPI (si instalas dependencias)

RATE_LIMIT_ENABLED=true
RATE_LIMIT_PROVIDER=slowapi
RATE_LIMIT_STORAGE_URI=redis://redis:6379/0


Requiere en backend/requirements.txt:

slowapi>=0.1.9
redis>=5.0


Política por defecto: 60 req/min al POST /chat y /api/chat.
Con SlowAPI, también dispones de GET /api/_rate_test.

🌐 Proxy Nginx y variantes sin proxy

Con proxy (recomendado): el frontend llama a /api, /rasa, /ws.

Sin proxy (dominios absolutos): usa admin_panel_react/.env.production.external o build args en el servicio admin del docker-compose.yml.

Más detalle en: admin_panel_react/README.md.

🐍 Entornos locales (.venv) – Backend / Rasa / React

Docker no necesita venvs. Esto es solo si vas a ejecutar servicios locales para depurar.

A) Backend en Python 3.12 (recomendado en Windows hoy)

cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000


B) Backend en Python 3.11 (si lo prefieres)

cd backend
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000


C) Rasa/Action Server local en 3.11 (solo si NO usas Docker para ellos)

# 1) Rasa (Terminal 1)
cd rasa
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip wheel
pip install rasa==3.6.* rasa-sdk==3.6.*
rasa train
rasa run --enable-api --cors "*" --port 5005

# 2) Actions (Terminal 2)
cd rasa
.\.venv\Scripts\Activate.ps1
python -m rasa_sdk --actions actions --port 5055


D) React (admin)
React no usa venv; usa Node LTS:

cd admin_panel_react
npm ci
npm run dev   # http://localhost:5173


Atajo: .\scripts\make_venvs.ps1 crea los venvs locales por ti (backend/Rasa).

🧪 QA / Smoke tests
1) Conexión

GET /api/chat/health → OK

GET /rasa/status → versión Rasa

GET / (backend) → mensaje OK

2) Intents
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/chat -Body (@{
  sender="qa-session"; message="hola"
} | ConvertTo-Json) -ContentType "application/json"

3) Forms

Mensaje: “necesito soporte” → completa slots → confirmación.

4) Tickets Helpdesk

HELPDESK_WEBHOOK=http://backend:8000/api/helpdesk/tickets (Action Server)

Ver confirmación en logs del backend.

5) Auth-gating

Sin token ⇒ utter_need_auth en intents protegidos.

Con token válido ⇒ flujo privado habilitado.

6) CORS/WS

Dev: 5173 → 8000 sin bloqueos.

Prod: WS por /ws (preferible wss:// con TLS).

7) Rate limit

Superar 60 req/min al chat devuelve 429.

📄 Para un detalle ampliado de pruebas (comandos + “resultado esperado” + plantilla de capturas) ver docs/QA-BACKEND.md.

🧯 Troubleshooting

Puertos ocupados: libera 80/443/8000/5005/5055/5173/6379 si están en uso.

Rasa no entrena: mira docker compose logs -f rasa. Con RASA_AUTOTRAIN=true entrena si no hay modelo.

Actions 404: ACTION_SERVER_URL debe apuntar a http://action-server:5055/webhook. Health: GET :5055/health.

CORS en dev: incluye http://localhost:5173 en ALLOWED_ORIGINS (backend).

Redis: verifica volumen redis-data y logs con docker compose logs -f redis.

Logs útiles

docker compose --profile build logs -f backend-dev rasa action-server nginx-dev
docker compose --profile prod  logs -f backend rasa action-server nginx

📚 Documentos locales (más guías)

Windows Quickstart: docs/WINDOWS-QUICKSTART.md ✅

Frontend (React/Vite): admin_panel_react/README.md

Rasa (bot + endpoints): rasa/README.md

Tareas Docker one-click: scripts/tasks.ps1

Crear entornos virtuales (venvs): scripts/make_venvs.ps1

QA Backend detallado (para informe): docs/QA-BACKEND.md