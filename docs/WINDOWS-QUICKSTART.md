# 🪟 Windows Quickstart — Chatbot Tutor Virtual

Guía express para levantar el proyecto en Windows (Visual Studio 2022 + PowerShell).
**No modifica la lógica de negocio.** Usa Docker para Rasa/Actions/Mongo/Nginx; el backend puedes correrlo en Docker o local con venv.

---

## ✅ Requisitos

- **Docker Desktop 4.x** (o Docker Engine + Compose v2)
- **Visual Studio 2022** (o VS Code) con terminal PowerShell
- **Node 18/20 LTS** (para desarrollo del panel React)
- **Python 3.12** (para backend local opcional) y **Python 3.11** (solo si corres Rasa/Actions fuera de Docker)
- Puertos libres: 80, 443, 8000, 5005, 5055, 5173, 6379

> Si PowerShell bloquea scripts locales, habilita por sesión:
>
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

---

## 📁 Dónde ejecutar los comandos

- **Raíz del repo**: `chatbot_tutor_virtual_v7.3\`
- **Backend**: `chatbot_tutor_virtual_v7.3\backend\`
- **Frontend (React)**: `chatbot_tutor_virtual_v7.3\admin_panel_react\`

Abre Visual Studio 2022 → *View* → *Terminal* → selecciona **PowerShell**.  
Usa `cd` para moverte a las rutas indicadas arriba.

---

## 🧰 Atajos “one-click”

### A) Tareas de orquestación (Docker)

- Script: **`.\scripts\tasks.ps1`**  
  Ruta: `chatbot_tutor_virtual_v7.3\scripts\tasks.ps1`

```powershell
# DEV/BUILD (HMR + proxy + logs)
.\scripts\tasks.ps1 -Profile build -Rebuild

# PROD (imágenes inmutables + proxy Nginx)
.\scripts\tasks.ps1 -Profile prod -Rebuild

# Solo ver logs
.\scripts\tasks.ps1 -Profile build -Logs
.\scripts\tasks.ps1 -Profile prod  -Logs

# Detener
.\scripts\tasks.ps1 -Profile build -Down
.\scripts\tasks.ps1 -Profile prod  -Down
B) Creación de entornos virtuales (venv)
Script: .\scripts\make_venvs.ps1 ✅ (Enlace directo)
Ruta: chatbot_tutor_virtual_v7.3\scripts\make_venvs.ps1

powershell
Copiar código
# Backend 3.12 (recomendado) — por defecto
.\scripts\make_venvs.ps1

# Backend 3.11 (opcional)
.\scripts\make_venvs.ps1 -Backend311

# Rasa/Actions 3.11 locales (solo si NO usas Docker para ellos)
.\scripts\make_venvs.ps1 -Rasa311
🚦 Modo 1 — Todo en Docker (DEV / perfil build)
Ejecuta desde la raíz del repo:

powershell
Copiar código
docker compose --profile build up -d mongo action-server rasa backend-dev admin-dev nginx-dev
docker compose --profile build logs -f backend-dev rasa action-server
UI (admin): http://localhost/

FastAPI docs: http://localhost:8000/docs

Rasa status: http://localhost:5005/status

Action Server health: http://localhost:5055/health

Alternativa: .\scripts\tasks.ps1 -Profile build -Rebuild

🛡️ Modo 2 — Producción local (perfil prod)
Desde la raíz:

powershell
Copiar código
docker compose --profile prod build
docker compose --profile prod up -d
docker compose --profile prod logs -f nginx backend rasa action-server
Admin: http://localhost/

API: http://localhost/api

Rasa: http://localhost/rasa (WS: ws://localhost/ws)

🐍 Modo 3 — Backend local (venv) + Resto en Docker
Levanta dependencias en Docker (raíz):

powershell
Copiar código
docker compose --profile build up -d mongo action-server rasa
Crea/activa venv del backend (carpeta backend):

powershell
Copiar código
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
(Opcional) UI dev (carpeta admin_panel_react):

powershell
Copiar código
cd ..\admin_panel_react
npm ci
npm run dev   # http://localhost:5173
Rasa/Actions permanecen en Docker, no necesitas venv 3.11 salvo que quieras correrlos locales.

🩺 Healthcheck rápido
Script en la raíz: .\check_health.ps1

powershell
Copiar código
.\check_health.ps1 `
  -FastApiUrl http://127.0.0.1:8000 `
  -RasaUrl    http://127.0.0.1:5005 `
  -ActionsUrl http://127.0.0.1:5055
Si todo OK abre /docs del backend automáticamente.

⏱️ Rate limit (activar por variables)
Sin tocar código. Edita docker-compose.yml:

Builtin (memoria):

yaml
Copiar código
environment:
  RATE_LIMIT_ENABLED: "true"
  RATE_LIMIT_PROVIDER: builtin
  RATE_LIMIT_BACKEND: memory
Builtin (Redis):

yaml
Copiar código
environment:
  RATE_LIMIT_ENABLED: "true"
  RATE_LIMIT_PROVIDER: builtin
  RATE_LIMIT_BACKEND: redis
  REDIS_URL: redis://redis:6379/0
Política por defecto: 60 req/min a POST /chat y /api/chat.

🧪 Smoke (3 líneas)
powershell
Copiar código
curl -fsS http://127.0.0.1:8000/chat/health
curl -fsS http://127.0.0.1:5005/status
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -Body (@{sender="qa";message="hola"} | ConvertTo-Json) -ContentType "application/json"
🧯 Problemas típicos
Puertos ocupados: libera 80/443/8000/5005/5055/5173/6379.

CORS en dev: ALLOWED_ORIGINS debe incluir http://localhost:5173.

Actions 404: confirma ACTION_SERVER_URL y health en :5055/health.

Rasa no entrena: RASA_AUTOTRAIN=true si no hay modelo; mira logs de rasa.

Redis: si lo usas, revisa volumen redis-data y logs del servicio.


