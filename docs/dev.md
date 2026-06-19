# 📘 README-dev — Chatbot Tutor Virtual (Desarrollo)

Este documento resume los pasos para:

- Desarrollar y depurar el **backend + Rasa** en local.
- Levantar el stack de **desarrollo con Docker** (`docker-compose.dev.yml`).
- (Opcional) Usar Visual Studio 2022 para ejecutar el backend.

---

## ⚠️ Nota sobre el Panel Administrativo (`admin_panel_react/`)

El proyecto incluye una carpeta `admin_panel_react/` con un panel administrativo (React + Vite).  
Sin embargo, en esta entrega:

- **No se implementa ni se valida funcionalmente** el panel administrativo.
- No se incluyen pruebas ni capturas del panel.
- Se mantiene como **mejora futura** que un desarrollador puede activar y adaptar.

Toda la parte crítica del trabajo se centra en:

- Backend FastAPI  
- Rasa + Action Server  
- MongoDB / Redis  
- Nginx (rutas del chatbot)  
- Autosave Guardian (si aplica)

---

## 🔧 1. Requisitos previos

- Python **3.11+** (recomendado).
- Node.js LTS (solo si quieres levantar el panel admin en dev).
- Docker Desktop (con docker compose v2) si vas a usar `docker-compose.dev.yml`.
- Visual Studio 2022 (opcional) con workload de **Desarrollo de Python**.

---

## 🚀 2. Levantar en local sin Docker (modo desarrollo puro)

### 🧠 2.1. Backend (FastAPI)

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip wheel
pip install -r requirements.txt

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
👉 Acceso:

Docs: http://127.0.0.1:8000/docs

Health: http://127.0.0.1:8000/health

🤖 2.2. Rasa + Action Server en local (opcional)
Si prefieres no usar Docker para Rasa en desarrollo:

Terminal 1 — Rasa
powershell
Copiar código
cd rasa
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -U pip wheel
pip install rasa==3.6.* rasa-sdk==3.6.*

rasa train
rasa run --enable-api --cors "*" --port 5005
Terminal 2 — Actions
powershell
Copiar código
cd rasa
.\.venv\Scripts\Activate.ps1
python -m rasa_sdk --actions actions --port 5055
🐳 3. Levantar con Docker – Desarrollo (docker-compose.dev.yml)
Para trabajar de forma más cercana al entorno de producción, se usa docker-compose.dev.yml.

3.1. Preparar el entorno
Desde la raíz del proyecto:

powershell
Copiar código
# Marca el modo DEV en el .env raíz (MODE=dev, etc.)
.\switch-env.ps1 dev
Asegúrate de tener .env.local con los valores por defecto para Docker local (Mongo, JWT, Rasa, etc.).

3.2. Levantar el stack de desarrollo
powershell
Copiar código
docker compose -f docker-compose.dev.yml up -d
Servicios típicos:

backend-dev → http://localhost:8000/docs

rasa → http://localhost:5005/status

action-server → puerto 5055

mongo → puerto 27017

redis-dev → puerto 6379 (si está configurado)

nginx-dev → http://localhost:8080 (proxy)

(opcional) admin-dev → http://localhost:5173 (panel React, no incluido en la entrega)

Ver logs:

powershell
Copiar código
docker compose -f docker-compose.dev.yml logs -f backend-dev rasa action-server
Apagar:

powershell
Copiar código
docker compose -f docker-compose.dev.yml down
💻 4. Visual Studio 2022 (F5) — Backend
Si trabajas con Visual Studio 2022, puedes configurar un perfil para lanzar FastAPI directamente.

4.1. Configuración típica
Intérprete: .venv\Scripts\python.exe

Script: módulo uvicorn con argumentos:

text
Copiar código
-m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
4.2. Ejemplo de launch.vs.json
En la raíz del repo (o de backend/), puedes crear .vs/launch.vs.json:

json
Copiar código
{
  "version": "0.2.1",
  "configurations": [
    {
      "type": "python",
      "name": "FastAPI (Uvicorn) - backend",
      "project": "backend",
      "pythonInterpreter": ".venv\\Scripts\\python.exe",
      "script": "-m",
      "args": [
        "uvicorn",
        "backend.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "workingDirectory": "."
    }
  ]
}
Después de esto, F5 → backend en http://127.0.0.1:8000/docs.

📂 5. Estructura relevante para desarrollo
text
Copiar código
.
├─ backend/              # FastAPI (API del chatbot)
│  ├─ main.py
│  ├─ api/, models/, core/, etc.
│  ├─ requirements.txt
│  ├─ .env.dev
│  └─ .env.production
├─ rasa/                 # Configuración de Rasa
│  ├─ domain.yml, nlu.yml, stories.yml, rules.yml
│  ├─ actions/
│  └─ Dockerfile
├─ autosave_guardian/    # (si aplica) lógica de guardian/autosave
├─ admin_panel_react/    # Panel admin (NO probado en esta entrega)
│  ├─ src/
│  ├─ vite.config.js
│  ├─ .env.development
│  └─ .env.production
├─ ops/nginx/            # Configs Nginx (dev/prod)
│  ├─ nginx.dev.conf
│  ├─ nginx.prod.conf
│  └─ conf.d/
├─ docker-compose.dev.yml
├─ docker-compose.prod.yml
├─ .env.local
├─ .env.root.dev
├─ .env.root.prod
├─ switch-env.ps1
└─ README-dev.md
🧪 6. Pruebas rápidas (smoke tests)
6.1. Backend vivo
powershell
Copiar código
Invoke-RestMethod -Method GET http://localhost:8000/health
6.2. Rasa vivo
powershell
Copiar código
Invoke-RestMethod -Method GET http://localhost:5005/status
6.3. Chat básico
powershell
Copiar código
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/chat `
  -Body (@{ sender="qa-session"; message="hola" } | ConvertTo-Json) `
  -ContentType "application/json"
6.4. Proxy Nginx (dev)
http://localhost:8080/api/chat/health

http://localhost:8080/rasa/status

🧯 7. Tips y problemas frecuentes
❌ No mezcles varios stacks a la vez
No levantes simultáneamente:

backend local en 8000

backend-dev (Docker) usando el mismo puerto.

❌ Errores de CORS en dev
Revisa ALLOWED_ORIGINS y EMBED_ALLOWED_ORIGINS en .env.local y en backend/.env.dev, incluye:

http://localhost:5173

http://localhost:8080

❌ Rasa sin modelo
Entrena con:

powershell
Copiar código
docker compose -f docker-compose.dev.yml exec rasa rasa train
❌ Mongo/Redis “corruptos” (solo en desarrollo, nunca en prod)

powershell
Copiar código
docker compose -f docker-compose.dev.yml down -v
⚠️ Esto borra datos de desarrollo (conversaciones, etc.).

📎 8. Panel Administrativo como mejora futura
Aunque el código del panel existe, para este entregable:

No se incluyen instrucciones para desplegarlo en producción.

No se realiza QA del panel.

No se documentan flujos de negocio en la UI admin.

Lo único que se deja claro es que, si alguien quiere activarlo en el futuro, tiene:

admin_panel_react/ con el código fuente React/Vite.

.env.development y .env.production como base de configuración.

Integración prevista vía Nginx (/, /chat, /embed, etc.).

La entrega se centra exclusivamente en el chatbot tutor virtual como backend conversacional, más la infraestructura necesaria (Rasa, Nginx, Mongo, Redis, Guardian).

9. Rasa Interactive (opción implementada)
Además del entrenamiento “clásico” (rasa train), durante el desarrollo se utilizó Rasa Interactive para depurar historias, flujos de diálogo e intents de forma guiada.

Rasa Interactive ya está soportado tanto:

🐍 En entorno local (venv de Rasa).

🐳 Dentro del contenedor Docker del servicio rasa, cuando el stack DEV/PROD está levantado.

🔎 Rasa Interactive no forma parte del uso diario en producción, pero sí se documenta como herramienta de soporte utilizada durante el desarrollo y ajuste del asistente.

9.1. Rasa Interactive en local (venv)
Requisitos previos:

Haber creado el entorno virtual de Rasa (sección 2 de este README).

Tener un modelo entrenado (rasa train ya ejecutado).

Pasos:

powershell
Copiar código
cd rasa
.\.venv\Scripts\Activate.ps1

# (opcional) validar datos antes
rasa data validate

# lanzar modo interactivo
rasa interactive
Esto abre una sesión en consola donde:

Puedes escribir mensajes como usuario.

Marcar qué intent es el correcto.

Corregir historias y reglas.

Guardar los cambios en los ficheros de entrenamiento (nlu, stories, rules).

Al finalizar, normalmente se vuelve a entrenar:

powershell
Copiar código
rasa train
9.2. Rasa Interactive dentro del contenedor Docker
También es posible usar Rasa Interactive desde el contenedor del servicio rasa.
La idea es:

Levantar el stack (DEV o PROD).

Entrar al contenedor de rasa.

Ejecutar rasa interactive desde dentro.

9.2.1. Levantar el stack (ejemplo DEV)
powershell
Copiar código
# Modo desarrollo
.\switch-env.ps1 dev
docker compose -f docker-compose.dev.yml up -d rasa action-server mongo
9.2.2. Entrar al contenedor e iniciar Rasa Interactive
Opción A – entrar a un shell y luego lanzar interactive:

powershell
Copiar código
# entrar en el contenedor rasa
docker compose -f docker-compose.dev.yml exec rasa bash

# ya dentro del contenedor:
cd /app/rasa     # (o el directorio de trabajo que uses dentro de la imagen)
rasa data validate   # opcional, valida datos
rasa interactive
Opción B – lanzar Rasa Interactive directamente:

powershell
Copiar código
docker compose -f docker-compose.dev.yml exec rasa rasa interactive
✅ Recomendación práctica:

Asegúrate de que el Action Server (action-server) también está levantado para que Rasa pueda ejecutar las acciones personalizadas durante la sesión interactiva.

Tras terminar y aplicar las correcciones que Rasa Interactive genera en los ficheros de entrenamiento, vuelve a ejecutar:

powershell
Copiar código
docker compose -f docker-compose.dev.yml exec rasa rasa train
9.3. Uso típico documentado en el proyecto
Durante el desarrollo de este chatbot tutor virtual:

Se utilizó Rasa Interactive para:

Afinar intents y entities en español.

Ajustar historias de soporte / tutoría.

Ver en tiempo real qué reglas y políticas se activaban.

Se empleó tanto:

En entorno local (venv), para pruebas rápidas.

Dentro del contenedor Docker de rasa, una vez levantado el stack DEV, para asegurar que el comportamiento en contenedor coincidiera con el entorno de despliegue.

Esto se deja documentado como herramienta de QA y refinamiento de NLU/NLG disponible para futuros mantenedores del proyecto.