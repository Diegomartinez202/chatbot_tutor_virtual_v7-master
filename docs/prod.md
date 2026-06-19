# 🚀 Guía de Despliegue en Producción (Chatbot Tutor Virtual)

Este documento describe cómo desplegar el **Chatbot Tutor Virtual** en un entorno de **producción local / VPS** usando `docker-compose.prod.yml`.

> ⚠️ **Importante sobre el Panel Administrativo (React/Vite)**  
> El proyecto incluye un panel administrativo (`admin_panel_react/`), pero en esta entrega:
> - **NO se despliega ni se evalúa** como parte del sistema en producción.
> - **NO se certifica su funcionamiento** en un entorno real (motivos: alcance, tiempo y seguridad).
> - El foco de la guía es el núcleo conversacional:
>   - Backend FastAPI  
>   - Rasa + Action Server  
>   - MongoDB / Redis  
>   - Autosave-Guardian (si está habilitado)  
>   - Nginx como reverse proxy  

---

## 🔧 Requisitos previos

- [Docker Engine](https://docs.docker.com/engine/) instalado en el servidor.  
- [Docker Compose v2+](https://docs.docker.com/compose/) habilitado (`docker compose version`).  
- Archivos de entorno configurados:

  - `.env.local` (en la raíz) → variables comunes para Docker (Mongo, JWT, Rasa, Redis, CORS, etc.).  
  - `.env.root.prod` → indica modo producción y qué `.env` usa el backend, por ejemplo:  
    ```env
    MODE=prod
    BACKEND_ENV_FILE=backend/.env.production
    ```
  - `backend/.env.production` → configuración interna del backend en modo producción  
    (URI de Mongo, JWT, CORS, SMTP, AWS, etc.).

> 🔒 Ninguno de estos archivos debe versionarse en Git. A partir de plantillas (`.env.example`, `.env.root.dev/.prod`) se construyen **copias locales**.

---

## 📂 Archivos clave para producción

- `docker-compose.prod.yml` → orquestación de servicios en entorno **PROD**:
  - `mongo`, `redis`, `rasa`, `action-server`, `autosave-guardian`, `backend`, `admin` (opcional) y `nginx-prod`.
- `ops/nginx/nginx.prod.conf` → configuración global de Nginx en producción.
- `ops/nginx/conf.d/prod/default.conf` → reverse proxy HTTP.
- `ops/nginx/conf.d/prod/prod-https.conf` → reverse proxy HTTPS (si se configuran certificados).
- `ops/nginx/conf.d/prod/includes/tls_params.conf` → parámetros TLS.
- `ops/nginx/certs/` → certificados TLS (`fullchain.pem`, `privkey.pem`).

---

## 🌐 Levantar todos los servicios en producción

En el servidor (o máquina donde se despliegue):

1. Confirmar que **no** está corriendo el entorno de desarrollo:

   ```bash
   docker compose -f docker-compose.dev.yml down
Asegurarse de tener .env.local, .env.root.prod y backend/.env.production configurados.

Construir y levantar el stack de producción:

bash
Copiar código
docker compose -f docker-compose.prod.yml up -d --build
Esto levantará, entre otros:

mongo

redis

rasa

action-server

autosave-guardian (si está definido)

backend

admin (panel React; opcional, no evaluado)

nginx-prod

🌍 Endpoints típicos en producción (local/VPS)
Asumiendo que nginx-prod expone:

80 → HTTP

443 → HTTPS (si configuras certificados)

Rutas habituales:

Servicio	URL aproximada
Proxy principal HTTP	http://localhost:8080 o dominio
API Backend (vía proxy)	http://localhost:8080/api
Rasa HTTP	http://localhost:8080/rasa
Rasa REST (proxy)	http://localhost:8080/api/chat/rasa/rest/webhook
WebSocket Rasa	ws://localhost:8080/ws (o wss:// con TLS)
Guardian (si aplica)	http://localhost:8080/guardian
Health Nginx	http://localhost:8080/ping

Si activas HTTPS con prod-https.conf y certificados válidos en ops/nginx/certs/,
podrás usar https://TU_DOMINIO y wss://TU_DOMINIO/ws.

🚀 Levantar servicios individuales (producción)
Generalmente se levanta todo el stack junto, pero también puedes iniciar servicios aislados:

bash
Copiar código
# Solo backend
docker compose -f docker-compose.prod.yml up -d backend

# Solo Rasa
docker compose -f docker-compose.prod.yml up -d rasa

# Solo Action Server
docker compose -f docker-compose.prod.yml up -d action-server

# Solo Nginx
docker compose -f docker-compose.prod.yml up -d nginx-prod
💡 Útil para reiniciar solo una pieza tras un cambio de configuración o imagen.

📜 Logs y monitoreo
Ver logs de todos los servicios:

bash
Copiar código
docker compose -f docker-compose.prod.yml logs -f
Ver solo logs de un servicio concreto (ejemplo: backend):

bash
Copiar código
docker compose -f docker-compose.prod.yml logs -f backend
Nginx (reverse proxy):

bash
Copiar código
docker compose -f docker-compose.prod.yml logs -f nginx-prod
Entrar a un contenedor en ejecución (ejemplo: backend):

bash
Copiar código
docker compose -f docker-compose.prod.yml exec backend sh
🧹 Mantenimiento y limpieza
Detener el stack de producción:

bash
Copiar código
docker compose -f docker-compose.prod.yml down
Detener y eliminar contenedores + volúmenes:

bash
Copiar código
docker compose -f docker-compose.prod.yml down -v
Reconstruir imágenes desde cero (sin caché):

bash
Copiar código
docker compose -f docker-compose.prod.yml build --no-cache
Limpiar recursos no utilizados (prune general):

bash
Copiar código
docker system prune -a
docker volume prune
docker network prune
⚠️ Cuidado: prune -a puede eliminar imágenes que estés usando para otros proyectos en el mismo servidor.

🔒 Seguridad y buenas prácticas
No subir *.env a Git (ya están en .gitignore).

Rotar regularmente:

Claves JWT (SECRET_KEY, JWT_SECRET),

Credenciales de Mongo / Redis (si se usan).

Usar siempre HTTPS en producción real:

Configurar fullchain.pem y privkey.pem en ops/nginx/certs/.

Revisar ops/nginx/conf.d/prod/prod-https.conf.

Restringir puertos expuestos en el servidor:

Idealmente expuesto solo el 80/443 (Nginx).

Mongo y Redis deben permanecer internos a la red Docker (app-net).

Configurar backups periódicos:

Dumps de MongoDB.

Snapshots de volúmenes en el proveedor (si aplica).

📝 Resumen rápido (checklist)
bash
Copiar código
# 1. Preparar entorno
#   - Crear .env.local
#   - Crear .env.root.prod (MODE=prod, BACKEND_ENV_FILE=backend/.env.production)
#   - Crear backend/.env.production

# 2. Apagar DEV si está arriba
docker compose -f docker-compose.dev.yml down

# 3. Construir y levantar PROD
docker compose -f docker-compose.prod.yml up -d --build

# 4. Ver logs
docker compose -f docker-compose.prod.yml logs -f nginx-prod backend rasa action-server

# 5. Probar:
#   - http://localhost:8080/ping
#   - http://localhost:8080/api/health
#   - http://localhost:8080/rasa/status
✍️ Autor: Diego Martínez
📌 Documento: Guía de despliegue en Producción para el Chatbot Tutor Virtual