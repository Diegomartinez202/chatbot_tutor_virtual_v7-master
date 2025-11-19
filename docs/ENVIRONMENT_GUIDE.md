🧩 Guía de Entornos — TutorBot (DEV / PROD)

Esta guía explica cómo funcionan los dos entornos del proyecto:

DEV → entorno de desarrollo local con hot-reload

PROD → entorno productivo detrás de Nginx (con opción a HTTPS)

Incluye los comandos correctos para levantarlos, detenerlos y limpiar redes, más la estructura actual de archivos de Nginx y Docker.

📁 Estructura de archivos relevante
tutorbot/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── admin_panel_react/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── rasa/
│   ├── Dockerfile
│   ├── actions/
│   └── models/
│
├── docker-compose.dev.yml
├── docker-compose.prod.yml
│
├── ops/
│   └── nginx/
│        ├── nginx.dev.conf          ← Nginx (DEV)
│        ├── nginx.prod.conf         ← Nginx (PROD)
│        ├── mime.types
│        └── conf.d/
│             ├── dev/
│             │     └── default.conf
│             └── prod/
│                   ├── default.conf
│                   ├── prod-https.conf
│                   ├── includes/
│                   │      └── tls_params.conf
│                   └── …
│
└── README.md

🚀 ENTORNO DEV (Desarrollo)
✔ Características

Backend con Uvicorn + reload

Frontend React con Vite + HMR

Rasa y Action Server activos

Todo servido detrás de nginx-dev

Navegación desde:
👉 http://localhost:8080

📦 Archivos que intervienen en DEV
Archivo	Rol
docker-compose.dev.yml	Orquesta backend-dev, admin-dev, rasa, action-server, nginx-dev
ops/nginx/nginx.dev.conf	Config principal de Nginx para desarrollo
ops/nginx/conf.d/dev/default.conf	Reverse proxy DEV (backend-dev, admin-dev, rasa)
▶ Cómo levantar DEV
1. Apaga cualquier stack activo (opcional pero recomendado)
docker compose down --remove-orphans


Si alguna red queda ocupada:

docker network ls
docker network rm <red>

2. Levantar el stack DEV
docker compose -f docker-compose.dev.yml up -d --build

3. Ver logs

Nginx DEV:

docker logs -f nginx-dev


Backend DEV:

docker logs -f backend-dev


Rasa:

docker logs -f rasa

4. Navegar
Servicio	URL
Frontend DEV	http://localhost:8080

Backend DEV directo	http://localhost:8002

Rasa API	http://localhost:8080/rasa

Health backend	http://localhost:8080/api/health

Rasa status	http://localhost:8080/rasa/status
⏹ Apagar DEV
docker compose -f docker-compose.dev.yml down

🛡 ENTORNO PROD (Producción)
✔ Características

Todo se ejecuta sin hot-reload

Nginx en modo reverse proxy (prod)

HTTPS opcional (prod-https.conf + certs)

Se puede activar por perfiles

📦 Archivos que intervienen en PROD
Archivo	Rol
docker-compose.prod.yml	Servicios productivos
ops/nginx/nginx.prod.conf	Config global Nginx para PROD
ops/nginx/conf.d/prod/default.conf	Reverse proxy HTTP
ops/nginx/conf.d/prod/prod-https.conf	Reverse proxy HTTPS
ops/nginx/conf.d/prod/includes/tls_params.conf	Parámetros TLS
ops/nginx/certs/	Certificados SSL
▶ Cómo levantar PRODUCCIÓN
1. Apaga DEV si está activo
docker compose -f docker-compose.dev.yml down

2. Levantar producción
docker compose -f docker-compose.prod.yml up -d --build


O si tienes perfiles:

docker compose --profile prod up -d --build

▶ Cómo probar PRODUCCIÓN
Servicio	URL
Frontend	http://localhost:8080

HTTPS (si activado)	https://localhost

Backend	http://localhost:8080/api

Rasa	http://localhost:8080/rasa

Health	http://localhost:8080/ping
⏹ Apagar PRODUCCIÓN
docker compose -f docker-compose.prod.yml down


o si usas perfiles:

docker compose --profile prod down

🧹 LIMPIEZA

Eliminar contenedores, imágenes y redes no usadas:

docker system prune -a


Eliminar solo redes huérfanas:

docker network prune

🔍 Problemas frecuentes
❌ “port already allocated 8000”

Alguien está ocupando el puerto.

Solución:

docker ps
docker stop <contenedor>


o cambiar el mapeo en docker-compose.dev.yml:

ports:
  - "8002:8000"

❌ Red en uso: “resource is still in use”

Significa que quedan contenedores unidos a esa red.

Ver contenedores en la red:

docker network inspect tutorbot-local_app-net


Luego:

docker stop <nombres>
docker rm <nombres>
docker network rm tutorbot-local_app-net

🎯 Recomendación final

Usa DEV solo para desarrollo local.

Usa PROD solo cuando quieras probar el entorno completo como servirá al usuario final.

Mantén Nginx organizado en:

dev/default.conf

prod/default.conf

prod/prod-https.conf (listo pero no habilitado por defecto)