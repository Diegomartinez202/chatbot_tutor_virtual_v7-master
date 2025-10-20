📘 README-dev.md — Chatbot Tutor Virtual v7.3

Este documento resume los pasos para levantar el proyecto en local, con Docker y en Visual Studio 2022 (F5).

🔧 1. Requisitos previos

Python 3.11+

Node.js LTS (npm incluido)

Docker Desktop (con docker compose v2)

Visual Studio 2022 con workloads:

Desarrollo de Python

(Opcional) Desarrollo de Node.js para Task Runner

🚀 2. Levantar en local (sin Docker)
Backend (FastAPI)
cd chatbot_tutor_virtual_v7.3
.venv\Scripts\activate
python -m pip install -r backend\requirements.txt --no-cache-dir
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
👉 Docs: http://127.0.0.1:8000/docs

Frontend (React + Vite)
cd admin_panel_react
npm install
npm run dev
👉 App: http://localhost:5173

🐳 3. Levantar con Docker Compose
Perfiles disponibles

build → usa tus Dockerfiles (./backend, ./rasa, ./rasa_action_server, ./admin_panel_react, ./ops/nginx).

vanilla → usa imágenes oficiales y monta tu código (./backend, ./rasa, ./rasa/actions).

Comandos rápidos
# Modo build
docker compose --profile build up -d --build

# Modo vanilla
docker compose --profile vanilla up -d --build

# Apagar
docker compose down

# Logs
docker compose --profile build logs -f backend


👉 Servicios:

Backend: http://localhost:8000/docs

Rasa: http://localhost:5005/status

Admin (React, solo build): http://localhost:8080

Nginx (solo build): http://localhost

🖥️ 4. Visual Studio 2022 (F5)
Si abriste la solución .sln

Startup project: backend

Startup File: main.py

Script Arguments:

-m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000


Interpreter: .venv\Scripts\python.exe

Si abriste solo la carpeta backend/

Crea el archivo .vs\launch.vs.json en la raíz:

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


Presiona F5 → inicia el backend en http://127.0.0.1:8000/docs
.

📜 5. Scripts útiles (doble clic)

run_backend.bat → activa .venv y levanta FastAPI.

run_frontend.bat → levanta React (npm run dev).

run_all.bat → abre backend + frontend en 2 ventanas.

run_compose_build.bat → menú up/down/logs/rebuild para perfil build.

run_compose_vanilla.bat → menú up/down/logs/rebuild para perfil vanilla.

check_health.bat y check_health.ps1 → testean /ping, /chat/health, /status.

train_rasa.bat y train_rasa.ps1 → validan datos y entrenan modelo en un clic ✅.

📂 6. Estructura relevante
chatbot_tutor_virtual_v7.3/
│── backend/              # FastAPI
│── rasa/                 # NLU/NLG (nlu.yml, stories.yml, rules.yml, domain.yml)
│── rasa_action_server/   # Custom actions
│── admin_panel_react/    # Panel admin (Vite + React)
│── ops/nginx/conf.d/     # Nginx configs
│── docker-compose.yml    # Orquestación con perfiles
│── run_backend.bat
│── run_frontend.bat
│── run_all.bat
│── run_compose_build.bat
│── run_compose_vanilla.bat
│── check_health.bat
│── check_health.ps1
│── train_rasa.bat        # ✅ Nuevo: valida + entrena Rasa
│── train_rasa.ps1        # ✅ Nuevo: valida + entrena Rasa
│── README-dev.md         # (este documento)

🛠️ 7. Tips

No mezcles perfiles de compose (build y vanilla) al mismo tiempo.

Usa docker compose ps para ver contenedores levantados.

Si Rasa dice No model found, entrena manualmente:

docker exec -it ctv_rasa rasa train


Revisa .env en la raíz para las credenciales de vanilla.

⚡ Scripts automáticos añadidos
train_rasa.bat
@echo off
echo === Validando datos Rasa ===
docker exec -it ctv_rasa rasa data validate --fail-on-warning
if %errorlevel% neq 0 (
    echo ❌ Error en validacion de datos
    pause
    exit /b %errorlevel%
)
echo === Entrenando modelo Rasa ===
docker exec -it ctv_rasa rasa train
pause

train_rasa.ps1
Write-Host "=== Validando datos Rasa ===" -ForegroundColor Cyan
docker exec -it ctv_rasa rasa data validate --fail-on-warning
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en validación de datos" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "=== Entrenando modelo Rasa ===" -ForegroundColor Green
docker exec -it ctv_rasa rasa train


✅ Con esto ya tienes todo el flujo completo:

Documentación actualizada.

Scripts rápidos para entrenar Rasa en un clic.

Proyecto listo para levantar en local, Docker o Visual Studio.

🌐 8. Nginx-dev (perfil build)

El servicio nginx-dev actúa como proxy inverso para tu entorno de desarrollo. Se levanta solo con el perfil build.

👉 Accesos rápidos:

Nginx-dev: http://localhost

Backend FastAPI: http://localhost:8000/docs

Rasa: http://localhost:5005/status

Admin React: http://localhost:8080

Comandos
# Levantar nginx-dev junto al resto de servicios (perfil build)
docker compose --profile build up -d --build nginx-dev

# Ver logs en vivo de nginx-dev
docker compose logs -f nginx-dev

# Reiniciar nginx-dev (sin tocar otros servicios)
docker compose restart nginx-dev

# Apagar solo nginx-dev
docker compose stop nginx-dev


⚠️ Tips:

nginx-dev solo existe en el perfil build.

Si lo levantas con docker compose --profile vanilla, no aparecerá.

Úsalo para probar el routing completo con proxy en local.

---

## ⚙️ Guía de perfiles Docker (Desarrollo / Build / Producción)

Este proyecto incluye varios perfiles de ejecución configurados en `docker-compose.override.yml` y `docker-compose.yml`.  
Cada perfil permite levantar únicamente los servicios necesarios para cada entorno, evitando sobrecargar el sistema.

| Perfil | Propósito | Comando para iniciar | Comando para detener | Comando para limpiar |
|:--|:--|:--|:--|:--|
| 🧩 **vanilla** | Solo Rasa + Mongo + Redis (modo base, sin build ni prod) | `docker compose --profile vanilla up -d` | `docker compose --profile vanilla down` | `docker compose --profile vanilla down -v --remove-orphans` |
| 🧱 **build** | Compila e instala dependencias para desarrollo | `docker compose --profile build up -d --build` | `docker compose --profile build down` | `docker compose --profile build down -v --remove-orphans` |
| 🚀 **prod** | Entorno productivo listo para despliegue | `docker compose --profile prod up -d` | `docker compose --profile prod down` | `docker compose --profile prod down -v --remove-orphans` |

### 🧰 Comandos útiles
```bash
# Ver servicios activos
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Reiniciar solo Rasa
docker compose restart rasa
📘 Consulta también el archivo README.ops.md para instrucciones de mantenimiento avanzado (backup de MongoDB, limpieza de Redis, healthchecks, etc.).

yaml
Copiar código

---

#### 📚 **Bloque para `README.md` (general)**
(agregar al final del archivo, justo antes del cierre o debajo de “Licencia / Créditos”)

```markdown
---

## 🧭 Guía rápida de ejecución por perfiles

Este proyecto puede levantarse con diferentes perfiles Docker, según el entorno deseado:

| Perfil | Descripción | Archivo de referencia |
|:--|:--|:--|
| 🧩 **vanilla** | Solo servicios base (Rasa + Mongo + Redis) | [`README.dev.md`](./README.dev.md) |
| 🧱 **build** | Entorno de desarrollo con dependencias y herramientas de build | [`README.dev.md`](./README.dev.md) |
| 🚀 **prod** | Entorno productivo estable para despliegue | [`README.ops.md`](./README.ops.md) |

Para más detalles y comandos específicos de cada perfil, revisa:

- 📘 **Desarrollo:** [`README.dev.md`](./README.dev.md)  
- ⚙️ **Operaciones:** [`README.ops.md`](./README.ops.md)

---

---

## 🐳 Despliegue con Docker y Perfiles

El proyecto está configurado para ejecutarse mediante **Docker Compose**, con distintos **perfiles** que controlan qué servicios se levantan según el entorno.

### 📦 Perfiles disponibles

| Perfil | Descripción | Servicios incluidos |
|:-------|:-------------|:--------------------|
| **dev** | Entorno de desarrollo | backend, frontend, rasa, action-server, mongo, redis |
| **prod** | Entorno de producción | backend, admin, rasa, action-server, mongo, redis |
| **build** | Solo construcción de imágenes | backend, admin |

### 🚀 Levantar servicios según el perfil

#### ➤ Entorno de desarrollo
```bash
docker compose --profile dev up -d
➤ Entorno de producción
bash
Copiar código
docker compose --profile prod up -d
➤ Construcción de imágenes sin ejecución
bash
Copiar código
docker compose --profile build build
🧩 Levantar servicios individuales
bash
Copiar código
docker compose --profile dev up -d backend
docker compose --profile dev up -d rasa
docker compose --profile dev up -d action-server
docker compose --profile dev up -d admin
📜 Logs y monitoreo
bash
Copiar código
# Ver todos los logs
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
🧹 Limpieza y mantenimiento
bash
Copiar código
# Detener todos los servicios
docker compose down

# Eliminar volúmenes y contenedores
docker compose down -v

# Reconstruir imágenes desde cero
docker compose build --no-cache
💡 Tip: Antes de levantar el entorno, asegúrate de haber configurado correctamente las variables de entorno (.env, .env.dev, .env.prod).

yaml
Copiar código
