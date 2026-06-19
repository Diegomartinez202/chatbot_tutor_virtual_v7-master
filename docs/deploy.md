# 🚀 Chatbot Tutor Virtual – Despliegue (DEV / PROD) con Docker

Stack principal:

- 🧠 **Backend**: FastAPI (Python)
- 🤖 **Rasa**: NLU + diálogo
- ⚙️ **Action Server**: acciones personalizadas
- 🗄️ **MongoDB**: almacenamiento de conversaciones y autosaves
- 🧱 **Redis**: rate-limit / cache (en prod)
- 🌐 **Nginx**: reverse proxy / TLS
- (📊 **Admin Panel React/Vite**: presente en el código, pero **no forma parte de la entrega** – ver nota)

Este documento **no modifica la lógica de negocio**: solo explica cómo levantar y operar el proyecto con Docker.

---

## ⚠️ Nota importante sobre el Panel Administrativo (`admin_panel_react/`)

En este trabajo de grado / entrega:

> 🔒 **El panel administrativo (carpeta `admin_panel_react/`) no se implementa ni se prueba como parte del producto entregado.**  
> Motivos: **seguridad, tiempo y alcance** del proyecto.  
> El código del panel se conserva como **mejora futura**, para quien quiera activarlo y extender el sistema.

Concretamente:

- En **desarrollo** (`docker-compose.dev.yml`), el servicio `admin-dev` (Vite) existe, pero **no es obligatorio levantarlo**.
- En **producción** (`docker-compose.prod.yml`), el servicio `admin` (build React servido por Nginx) existe, pero **no se considera parte del alcance probado**.
- Toda la validación y pruebas descritas en la documentación se centran en:
  - Backend FastAPI
  - Rasa
  - Action Server
  - Autosave Guardian (si aplica)
  - Mongo / Redis
  - Nginx (reverse proxy + rutas del chatbot)

---

## 📚 Índice

1. [Perfiles / Modos de ejecución](#-perfiles--modos-de-ejecución)  
2. [Estructura del repo](#-estructura-del-repo)  
3. [Prerrequisitos](#-prerrequisitos)  
4. [Configuración de entornos (.env y switch-env.ps1)](#-configuración-de-entornos-env-y-switch-envps1)  
5. [Comandos rápidos de despliegue](#-comandos-rápidos-de-despliegue)  
6. [Health / Endpoints clave](#-health--endpoints-clave)  
7. [Rate limit por configuración](#-rate-limit-por-configuración)  
8. [Notas sobre desarrollo local sin Docker (opcional)](#-notas-sobre-desarrollo-local-sin-docker-opcional)  
9. [Troubleshooting básico](#-troubleshooting-básico)  
10. [Chuleta de comandos Docker](#-chuleta-de-comandos-docker)  

---

## 🧩 Perfiles / Modos de ejecución

Actualmente el proyecto se despliega con **dos archivos Compose separados**:

- `docker-compose.dev.yml`  → **entorno de desarrollo**
- `docker-compose.prod.yml` → **entorno de producción / entrega**

Además, existe un `.env.local` en la raíz que contiene configuración común para Docker (Mongo, Redis, JWT, Rasa, Nginx, etc.), y un script `switch-env.ps1` que ajusta el `.env` raíz para indicar si estás en **dev** o **prod**.

### 🔹 DEV – `docker-compose.dev.yml`

Servicios típicos:

- `backend-dev` → FastAPI con `uvicorn --reload`
- `rasa` → motor Rasa (con acciones en `action-server`)
- `action-server` → servidor de acciones de Rasa
- `mongo` → base de datos
- `redis-dev` → Redis en entorno de desarrollo (si está definido)
- `autosave-guardian` → API de guardian/autosave (si está activada)
- `nginx-dev` → reverse proxy local (`http://localhost:8080`)
- `admin-dev` → (opcional) panel React en modo Vite (`http://localhost:5173`)

### 🔹 PROD – `docker-compose.prod.yml`

Servicios típicos:

- `mongo`
- `redis`
- `rasa`
- `action-server`
- `autosave-guardian`
- `backend` → FastAPI modo producción (Uvicorn)
- `admin` → build del panel React (⚠️ **no probado en esta entrega**)
- `nginx-prod` → reverse proxy + TLS (`http://localhost:8080` y `https://localhost` si hay certificados)

---

## 🗂️ Estructura del repo

Solo lo relevante para despliegue:

```text
.
├─ backend/                      # FastAPI (API del chatbot)
│  ├─ main.py                    # punto de entrada
│  ├─ requirements.txt
│  ├─ .env.dev                   # entorno backend DEV
│  ├─ .env.production / .env.prod# entorno backend PROD (Docker)
├─ rasa/                         # Bot Rasa (NLU / historias / dominio)
│  ├─ Dockerfile
│  ├─ domain.yml, nlu.yml, etc.
│  └─ actions/                   # acciones personalizadas
├─ autosave_guardian/            # (si aplica) Guardian / autosave (Flask)
├─ admin_panel_react/            # Panel admin (NO incluido en la entrega)
│  ├─ Dockerfile
│  ├─ vite.config.js
│  ├─ .env.development
│  └─ .env.production
├─ ops/nginx/                    # Configuración Nginx
│  ├─ nginx.dev.conf
│  ├─ nginx.prod.conf
│  └─ conf.d/
│     ├─ dev/default.conf
│     ├─ prod/default.conf
│     └─ prod/prod-https.conf
├─ docker-compose.dev.yml        # Stack completo DEV
├─ docker-compose.prod.yml       # Stack completo PROD
├─ .env.local                    # entorno Docker local (Mongo, JWT, etc.)
├─ .env.root.dev                 # plantilla raíz para MODO=dev
├─ .env.root.prod                # plantilla raíz para MODO=prod
├─ switch-env.ps1                # script para alternar DEV/PROD
└─ README-deploy.md              # este documento
✅ Prerrequisitos
Docker Desktop (Windows) o Docker Engine + docker compose v2

PowerShell (en Windows) para usar switch-env.ps1

Puertos libres recomendados:

8080 → Nginx (proxy dev/prod)

8000 → FastAPI directo (dev)

5005 → Rasa

5055 → Action Server

27017 → Mongo

6379 → Redis

5173 → Vite (solo si usas admin-dev)

🧱 Configuración de entornos (.env y switch-env.ps1)
🌐 1) .env.local (raíz)
Es el archivo con la configuración común para Docker local:

Conexión a Mongo:

MONGO_URI, MONGO_DB, MONGO_AUTOSAVE_COLLECTION, MONGO_SECURITY_LOGS_COLLECTION, etc.

Seguridad:

JWT_SECRET, JWT_ALG, JWT_ISSUER, JWT_AUDIENCE

Integración Rasa:

RASA_URL, ACTION_SERVER_URL, TRACKER_MONGO_URL

Chat / frontend:

VITE_API_BASE, VITE_CHAT_REST_URL, VITE_RASA_REST_URL, VITE_RASA_WS_URL, etc.

CORS / Embed:

ALLOWED_ORIGINS, EMBED_ALLOWED_ORIGINS, FRAME_ANCESTORS, FRONTEND_SITE_URL

Rate limit:

RATE_LIMIT_ENABLED, RATE_LIMIT_BACKEND, REDIS_URL, RATE_LIMIT_MAX_REQUESTS, etc.

👉 No toques la lógica, solo ajusta valores (por ejemplo, dominios reales en PROD).

🔁 2) .env.root.dev / .env.root.prod + switch-env.ps1
.env.root.dev:

env
Copiar código
MODE=dev
BACKEND_ENV_FILE=backend/.env.dev
COMPOSE_PROFILES=
.env.root.prod:

env
Copiar código
MODE=prod
BACKEND_ENV_FILE=backend/.env.production
COMPOSE_PROFILES=prod
El script:

powershell
Copiar código
.\switch-env.ps1 dev
.\switch-env.ps1 prod
reescribe el .env raíz para que las herramientas (y, si quisieras, docker compose --env-file) sepan en qué modo estás trabajando.

▶️ Comandos rápidos de despliegue
🧪 Entorno de desarrollo (DEV)
Desde la raíz del proyecto:

powershell
Copiar código
# 1) Marca el modo DEV en el .env raíz
.\switch-env.ps1 dev

# 2) Levanta todo el stack de desarrollo
docker compose -f docker-compose.dev.yml up -d

# 3) Ver logs (ejemplo: backend, rasa, action-server, nginx-dev)
docker compose -f docker-compose.dev.yml logs -f backend-dev rasa action-server nginx-dev
Accesos típicos:

Proxy dev (Nginx): http://localhost:8080

Backend FastAPI (directo): http://localhost:8000/docs

Rasa (directo): http://localhost:5005/status

Action Server: http://localhost:5055/health (si está implementado)

(Opcional) Panel admin dev (Vite): http://localhost:5173
⚠️ No se valida ni se entrega funcionalmente en este proyecto.

Apagar:

powershell
Copiar código
docker compose -f docker-compose.dev.yml down
🚀 Entorno de producción (PROD – local / VPS)
powershell
Copiar código
# 1) Marca el modo PROD en el .env raíz
.\switch-env.ps1 prod

# 2) Levanta el stack de producción
docker compose -f docker-compose.prod.yml up -d

# 3) Logs (Nginx + backend + Rasa + actions)
docker compose -f docker-compose.prod.yml logs -f nginx-prod backend rasa action-server
Accesos típicos:

Proxy prod (HTTP): http://localhost:8080

(Si tienes TLS configurado) https://localhost (o el dominio real)

API vía proxy: http://localhost:8080/api

Chat REST: http://localhost:8080/api/chat

Rasa vía proxy: http://localhost:8080/rasa

WebSocket: ws://localhost:8080/ws (o wss:// con TLS)

Apagar:

powershell
Copiar código
docker compose -f docker-compose.prod.yml down
🩺 Health / Endpoints clave
🧠 Backend FastAPI
GET / → mensaje simple de “API OK”

GET /health → {"ok": true}

GET /docs → Swagger UI directo

Vía Nginx (según mapeo):

GET /api/health

GET /api/docs

Chat:

GET /api/chat/health

POST /api/chat
(rate limited según las variables de entorno)

🤖 Rasa
Directo: GET http://localhost:5005/status

Vía proxy: GET http://localhost:8080/rasa/status (si está mapeado en Nginx)

⚙️ Action Server
Normalmente: GET http://localhost:5055/health (si la ruta está implementada)

⏱️ Rate limit por configuración
Todo el rate limit se controla por variables de entorno (no hay que cambiar código):

env
Copiar código
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=redis   # o memory
RATE_LIMIT_PROVIDER=builtin
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_WINDOW_SEC=60
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_KEY_STRATEGY=user_or_ip
Por defecto se limitan las peticiones al chat (POST /chat, /api/chat) a 60 req/minuto.

En desarrollo puedes usar memory.

En producción se recomienda redis.

🐍 Notas sobre desarrollo local sin Docker (opcional)
Para depuración avanzada, puedes ejecutar servicios sin Docker.

Backend (FastAPI) local
powershell
Copiar código
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
Rasa local (solo NLU/bot)
powershell
Copiar código
cd rasa
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install rasa==3.6.* rasa-sdk==3.6.*
rasa train
rasa run --enable-api --cors "*" --port 5005
Para detalles de desarrollo local, ver también README-dev.md.

🧯 Troubleshooting básico
❌ Puerto ocupado
Usa netstat / Get-NetTCPConnection para ver qué está usando 8080, 8000, 5005, 5055, etc.

❌ Rasa no arranca / no hay modelo
Revisa logs:

powershell
Copiar código
docker compose -f docker-compose.dev.yml logs -f rasa
Y entrena si hace falta:

powershell
Copiar código
docker compose -f docker-compose.dev.yml exec rasa rasa train
❌ CORS en dev
Asegúrate de que ALLOWED_ORIGINS incluye http://localhost:5173 y http://localhost:8080.

❌ Redis no responde
Revisa el servicio redis en docker-compose.prod.yml y su volumen, y mira logs:

powershell
Copiar código
docker compose -f docker-compose.prod.yml logs -f redis
📌 Chuleta de comandos Docker
Comandos generales (aplican tanto a docker-compose.dev.yml como a docker-compose.prod.yml):

powershell
Copiar código
# Ver servicios activos
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.prod.yml ps

# Levantar todo el stack (dev/prod)
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.prod.yml up -d

# Reconstruir imágenes (sin cache)
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.prod.yml build --no-cache

# Ver logs en tiempo real
docker compose -f docker-compose.dev.yml logs -f
docker compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker compose -f docker-compose.dev.yml logs -f backend-dev
docker compose -f docker-compose.prod.yml logs -f backend

# Reiniciar un servicio
docker compose -f docker-compose.dev.yml restart rasa
docker compose -f docker-compose.prod.yml restart rasa

# Apagar y eliminar contenedores
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.prod.yml down

# Apagar + eliminar volúmenes y redes (⚠️ borra datos de Mongo/Redis)
docker compose -f docker-compose.dev.yml down -v --remove-orphans
docker compose -f docker-compose.prod.yml down -v --remove-orphans