## 📎 Integración en sitios externos 
Consulta la guía: [EMBED_GUIDE.md](./EMBED_GUIDE.md)

# 🤖 Chatbot Tutor Virtual v2 – Proyecto SENA

Sistema modular e inteligente para orientación académica y soporte en línea de preguntas frecuentes, desarrollado como solución embebible para plataformas educativas como **Zajuna**. Utiliza **FastAPI**, **Rasa**, **MongoDB**, **React** y **Docker**.

---
![Status](https://img.shields.io/badge/estado-desarrollo-blue.svg)
![Licencia](https://img.shields.io/badge/licencia-MIT-brightgreen.svg)
![Chatbot Rasa](https://img.shields.io/badge/Rasa-IA%20Conversacional-purple.svg)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)
![Panel React](https://img.shields.io/badge/Admin%20Panel-React%2BVite-blue.svg)
![Despliegue](https://img.shields.io/badge/despliegue-pendiente-lightgrey.svg)

<p align="center">
  <img src="https://img.shields.io/badge/Proyecto-SENA-008000?style=for-the-badge&logo=github" alt="Proyecto SENA" />
  <img src="https://img.shields.io/badge/Estado-En%20desarrollo-blue?style=for-the-badge" alt="Estado" />
  <img src="https://img.shields.io/github/license/Diegomartinez202/chatbot_tutor_virtual_v7?style=for-the-badge" alt="Licencia MIT" />
  <img src="https://img.shields.io/badge/Despliegue-Railway-grey?style=for-the-badge&logo=railway" alt="Railway" />
</p>

<div align="center">

![GitHub repo size](https://img.shields.io/github/repo-size/Diegomartinez202/chatbot_tutor_virtual_v7?label=Repo%20Size)
![GitHub last commit](https://img.shields.io/github/last-commit/Diegomartinez202/chatbot_tutor_virtual_v7?label=Last%20Commit)
![GitHub issues](https://img.shields.io/github/issues/Diegomartinez202/chatbot_tutor_virtual_v7)
![GitHub license](https://img.shields.io/github/license/Diegomartinez202/chatbot_tutor_virtual_v7)
![GitHub stars](https://img.shields.io/github/stars/Diegomartinez202/chatbot_tutor_virtual_v7?style=social)

</div>

---

# 📘 Proyecto Chatbot Tutor Virtual v7.3

## 🏫 Institución
**Servicio Nacional de Aprendizaje (SENA)**

## 👤 Autor
**Daniel Hernán Martínez Cano**

## 📅 Versión
v7.3 — 2025

---

## 🧩 Componentes del Proyecto

| Carpeta / Componente      | Tecnología           | Descripción                                                                 |
|---------------------------|----------------------|-----------------------------------------------------------------------------|
| `backend/`                | FastAPI + MongoDB    | API REST con autenticación JWT, gestión de intents, logs y usuarios        |
| `rasa/`                   | Rasa 3.6             | Motor conversacional con intents, reglas, slots y acciones personalizadas  |
| `rasa_action_server/`     | Rasa SDK             | Servidor de acciones personalizadas                                         |
| `admin-panel-react/`      | React + Vite         | Panel administrativo con login, intents, logs y estadísticas               |
| `static/widget/`          | HTML + JS            | Widget web embebible vía iframe/script                                     |
| `ops/nginx/conf.d/`       | Nginx                | Configuración de reverse proxy (dev/prod)                                   |
| `docker/`                 | Docker               | Configuración para contenedores, init Mongo, volúmenes                     |
| `.github/workflows/`      | GitHub Actions       | Despliegue continuo (CI/CD) en Railway                                     |
| `scripts/`                | Bash/PowerShell      | Automatización de tareas: build, test, deploy, backup                      |

---

## 📂 Estructura del Proyecto

```bash
chatbot_tutor_virtual_v7.3/
├── backend/                # FastAPI + conexión a MongoDB
├── rasa/                   # NLU/NLG (domain.yml, nlu.yml, rules.yml, stories.yml)
├── rasa_action_server/     # Custom actions de Rasa
├── admin_panel_react/      # Panel administrativo en React + Vite
├── static/widget/          # Widget embebido
├── ops/nginx/conf.d/       # Configuración de Nginx
├── docker/                 # Configuración inicial de contenedores
├── scripts/                # Scripts de automatización
├── .github/workflows/      # Workflows CI/CD
├── .env.example
├── docker-compose.yml
├── run_backend.bat
├── run_frontend.bat
├── run_all.bat
├── run_compose_build.bat
├── run_compose_vanilla.bat
├── check_health.bat
├── check_health.ps1
├── README.md               # Documento institucional
└── README-dev.md           # Guía técnica para desarrolladores
📌 Introducción
El Chatbot Tutor Virtual es una solución tecnológica diseñada para apoyar a los aprendices del SENA en la interacción con la plataforma Zajuna y en la gestión de procesos académicos y administrativos.

El proyecto combina:

🤖 IA Conversacional (Rasa NLU/NLG)

⚙️ Backend en FastAPI con MongoDB

📊 Panel administrativo en React (Vite)

💬 Widget embebible para sitios externos

🐳 Docker Compose para contenerización

🚀 Railway para despliegue CI/CD

🎯 Objetivos
Objetivo General
Desarrollar un Chatbot Tutor Virtual que facilite el acompañamiento académico, mejore la experiencia de los aprendices en la plataforma Zajuna y optimice los procesos de soporte.

Objetivos Específicos
Levantamiento de requerimientos funcionales y no funcionales.

Diseño de arquitectura modular y escalable.

Implementación del backend en FastAPI con autenticación JWT.

Integración de Rasa para flujos conversacionales inteligentes.

Desarrollo de un panel administrativo en React + Vite.

Construcción de un widget web embebible.

Pruebas unitarias y funcionales.

Contenerización con Docker Compose.

Documentación técnica e institucional.

🏗️ Arquitectura General
El sistema incluye:

Backend (FastAPI + MongoDB) – API REST, autenticación, comunicación con Rasa.

Rasa – Intenciones, reglas, acciones personalizadas.

Panel React (Vite) – Gestión de intents, usuarios y métricas.

Widget Web – Interfaz embebible.

Nginx – Reverse proxy y servidor estático.

Docker Compose – Orquestación con perfiles (build, prod, vanilla).

🚀 Instalación Local (modo desarrollo)
1. Clonar el repositorio
bash
Copiar código
git clone https://github.com/Diegomartinez202/chatbot_tutor_virtual_v7.git
cd chatbot_tutor_virtual_v7
2. Backend – FastAPI
bash
Copiar código
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
3. Motor de IA – Rasa

cd rasa
pip install rasa
rasa train
rasa run --enable-api --cors "*" --port 5005 --debug

🔄 Restauración de modelos Rasa (Backup)

Si necesitas volver a un modelo anterior, sigue estos pasos:

1️⃣ Listar backups disponibles

Los backups se encuentran en ./rasa/models_backup.

Windows:

dir .\rasa\models_backup


Linux/Mac:

ls -l ./rasa/models_backup


Se mostrarán carpetas con formato backup_YYYYMMDD_HHMMSS.

2️⃣ Restaurar un backup específico

Copia los modelos de la carpeta de backup a la carpeta principal de modelos (./rasa/models).

Windows:

xcopy /E /I /Y ".\rasa\models_backup\backup_20250930_213045\*" ".\rasa\models\"


Linux/Mac:

cp -r ./rasa/models_backup/backup_20250930_213045/* ./rasa/models/


Sustituye backup_20250930_213045 por el nombre del backup que quieres restaurar.

3️⃣ Verificar modelos restaurados

Windows:

dir .\rasa\models


Linux/Mac:

ls -l ./rasa/models


Confirma que los modelos se copiaron correctamente.

4️⃣ Re-entrenamiento opcional

Después de restaurar, si quieres actualizar con nuevos datos:

docker compose run --rm rasa rasa train --verbose


💡 Tip: Siempre haz un backup antes de restaurar para no perder los modelos actuales.

4. Panel Admin – React

cd admin-panel-react
npm install
npm run dev
💬 Widget Embebido
Puedes integrarlo en cualquier sitio como Zajuna:


<script src="https://TU_DOMINIO/static/widget/embed.js"></script>
O directamente:


<iframe src="https://TU_DOMINIO/static/widget/widget.html" width="400" height="600"></iframe>
🧪 Pruebas Automáticas

cd backend
pytest tests/
🐳 Despliegue con Docker Compose
El proyecto define tres perfiles en docker-compose.yml:

🔹 1. Modo BUILD (desarrollo con hot reload)
bash
Copiar código
docker compose --profile build up --build
Accesos:

Frontend: http://localhost:8080

Backend: http://localhost:8000/api

Rasa: http://localhost:5005

🔹 2. Modo PROD (producción optimizada)
bash
Copiar código
docker compose --profile prod up --build
Accesos:

Frontend: http://localhost

Backend API: http://localhost/api

Rasa HTTP: http://localhost/rasa

Rasa WebSocket: ws://localhost/ws

🔹 3. Modo VANILLA (imágenes oficiales sin build local)

docker compose --profile vanilla up
🔄 Scripts de Reset para Docker
Incluye 3 variantes (/scripts/):

reset_dev.ps1 → menú interactivo.

reset_dev_light.ps1 → ciclo completo + logs.

reset_dev_auto.ps1 → ciclo completo sin logs.

🌐 Despliegue en Railway (CI/CD)
Crear proyecto en Railway.

Conectar este repositorio.

Configurar variables de entorno (.env.example).

Railway ejecutará automáticamente el backend.

Workflows útiles:

.github/workflows/deploy_railway.yml

.github/workflows/train_rasa.yml




## 🌐 Configuración de Nginx (Dev y Prod)

En este proyecto, **Nginx** se utiliza como reverse proxy para servir el frontend, enrutar las peticiones al backend y a Rasa, y gestionar WebSockets.  
A continuación se muestran ejemplos de configuración para **desarrollo (dev)** y **producción (prod)**.

### 🔹 nginx.conf – Desarrollo (DEV)
Este archivo permite probar con hot reload de React (Vite) y FastAPI en modo debug.

```nginx
server {
  listen 80;
  server_name _;

  # ============================================================
  # Frontend (Vite en modo DEV)
  # ============================================================
  location / {
    proxy_pass http://admin-dev:5173;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # ============================================================
  # Backend (FastAPI DEV)
  # ============================================================
  location /api/ {
    rewrite ^/api/?(.*)$ /$1 break;
    proxy_pass http://backend-dev:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # ============================================================
  # Rasa HTTP API
  # ============================================================
  location /rasa/ {
    rewrite ^/rasa/?(.*)$ /$1 break;
    proxy_pass http://rasa:5005/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # ============================================================
  # Rasa WebSocket
  # ============================================================
  location /ws/ {
    proxy_pass http://rasa:5005/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
}
🔹 nginx.conf – Producción (PROD)
Este archivo sirve el frontend ya compilado de React y enruta las APIs.

nginx
Copiar código
server {
  listen 80;
  server_name _;

  # ============================================================
  # Frontend (React build)
  # ============================================================
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri /index.html;
  }

  # ============================================================
  # Backend (FastAPI PROD)
  # ============================================================
  location /api/ {
    rewrite ^/api/?(.*)$ /$1 break;
    proxy_pass http://backend:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # ============================================================
  # Rasa HTTP API
  # ============================================================
  location /rasa/ {
    rewrite ^/rasa/?(.*)$ /$1 break;
    proxy_pass http://rasa:5005/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # ============================================================
  # Rasa WebSocket
  # ============================================================
  location /ws/ {
    proxy_pass http://rasa:5005/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
}
📌 Notas importantes:

En DEV los servicios apuntan a backend-dev:8000 y admin-dev:5173.

En PROD los servicios usan los contenedores finales backend:8000 y nginx sirviendo React build desde /usr/share/nginx/html.

Ambos casos soportan WebSocket para Rasa (/ws).


🔹 1. Montar nginx.conf en docker-compose

En tu docker-compose.yml vamos a integrar el nginx.conf para que automáticamente se monte según el profile (dev o prod).

services:
  nginx:
    image: nginx:1.25-alpine
    container_name: nginx
    restart: always
    ports:
      - "80:80"
    volumes:
      # 🔹 frontend build en prod
      - ./admin_panel_react/dist:/usr/share/nginx/html:ro
      # 🔹 configuración Nginx (usa el mismo archivo para dev/prod)
      - ./ops/nginx/conf.d/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
      - rasa
    profiles: ["prod", "build"]


👉 En ops/nginx/conf.d/nginx.conf colocas el bloque que ya te dejé integrado en el README.md (tienes ambos: dev y prod, usas el que corresponda).

🔹 2. Volver a construir el contenedor de Nginx

Ejecuta:

docker compose --profile prod up -d --build nginx


o para desarrollo:

docker compose --profile build up -d --build nginx


Esto garantiza que Nginx levante con la nueva configuración.

🔹 3. Verificar que Nginx esté corriendo
docker ps


Debes ver nginx arriba.
Después prueba en el navegador:

Frontend: http://localhost

Backend: http://localhost/api

Rasa API: http://localhost/rasa

WebSocket Rasa: ws://localhost/ws

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


📜 Licencia
MIT — Uso libre académico e institucional.

🧠 Créditos
Desarrollado por Diego Martínez como solución de tutoría automatizada para aprendices del SENA.

Incluye integración con:

Plataforma Zajuna

Inteligencia Conversacional Rasa

Panel React

Docker + Railway