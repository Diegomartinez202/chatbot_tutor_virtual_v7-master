# 🧩 Guía de Entornos — Chatbot Tutor Virtual (DEV / PROD)
Esta guía explica cómo funcionan los dos entornos principales del proyecto:

- **DEV** → entorno de desarrollo local con hot-reload y proxy Nginx.  
- **PROD** → entorno productivo local/VPS detrás de Nginx (con opción a HTTPS).

Incluye:

- Comandos para levantar / detener cada entorno.  
- Archivos de Nginx y Docker que intervienen.  
- Problemas frecuentes y cómo diagnosticarlos.

---

## 📁 Estructura de archivos relevante

```text
chatbot_tutor_virtual/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.dev
│   └── .env.production
│
├── admin_panel_react/
│   ├── src/
│   ├── package.json
│   └── Dockerfile       # Panel admin (NO evaluado; mejora futura)
│
├── rasa/
│   ├── Dockerfile
│   ├── actions/
│   └── models/
│
├── autosave_guardian/
│   ├── app.py
│   └── requirements.txt
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
├── .env.local
├── .env.root.dev
├── .env.root.prod
│
└── README.md
⚠️ El panel admin_panel_react/ existe pero no se despliega ni se evalúa en esta entrega.
Se mantiene documentado como mejora futura opcional.

🚀 ENTORNO DEV (Desarrollo)
✔ Características
Backend corriendo con Uvicorn + --reload (backend-dev).

Rasa + Action Server activos en contenedores.

MongoDB (y Redis si se requiere) en contenedores.

Todo servido detrás de nginx-dev.

Navegación principal desde:
👉 http://localhost:8080

📦 Archivos que intervienen en DEV
Archivo	Rol
docker-compose.dev.yml	Orquesta backend-dev, rasa, action-server, mongo, redis-dev, autosave-guardian, nginx-dev (y opcionalmente admin-dev)
ops/nginx/nginx.dev.conf	Config principal de Nginx para desarrollo
ops/nginx/conf.d/dev/default.conf	Reverse proxy DEV (/api, /rasa, /ws)

▶ Cómo levantar DEV
(Opcional, pero recomendado) Apagar cualquier stack activo:

bash
Copiar código
docker compose -f docker-compose.prod.yml down
Marcar el modo DEV en el .env raíz (si usas switch-env.ps1):

powershell
Copiar código
.\switch-env.ps1 dev
Levantar el stack DEV:

bash
Copiar código
docker compose -f docker-compose.dev.yml up -d --build
Ver logs:

bash
Copiar código
# Nginx DEV
docker compose -f docker-compose.dev.yml logs -f nginx-dev

# Backend DEV
docker compose -f docker-compose.dev.yml logs -f backend-dev

# Rasa
docker compose -f docker-compose.dev.yml logs -f rasa
🌍 URLs típicas en DEV
Servicio	URL
Proxy DEV (Nginx)	http://localhost:8080
Backend DEV directo	http://localhost:8000/docs (si expuesto)
Rasa API (proxy)	http://localhost:8080/rasa
Rasa status (proxy)	http://localhost:8080/rasa/status
Health backend	http://localhost:8080/api/health

El panel admin-dev (Vite) puede estar disponible en http://localhost:5173 si lo configuras,
pero no se incluye en las pruebas oficiales de esta entrega.

⏹ Apagar DEV
bash
Copiar código
docker compose -f docker-compose.dev.yml down
Si quieres eliminar también volúmenes de desarrollo:

bash
Copiar código
docker compose -f docker-compose.dev.yml down -v
🛡 ENTORNO PROD (Producción local / VPS)
✔ Características
FastAPI (backend) corriendo en modo producción (sin --reload).

Rasa y Action Server en contenedores dedicados.

MongoDB + Redis (para rate limit).

Nginx en modo reverse proxy (nginx-prod), con posibilidad de HTTPS.

Panel admin (admin) disponible a nivel de contenedor, pero fuera del alcance evaluado.

📦 Archivos que intervienen en PROD
Archivo	Rol
docker-compose.prod.yml	Orquesta servicios productivos
ops/nginx/nginx.prod.conf	Config global Nginx para PROD
ops/nginx/conf.d/prod/default.conf	Reverse proxy HTTP
ops/nginx/conf.d/prod/prod-https.conf	Reverse proxy HTTPS (opcional)
ops/nginx/conf.d/prod/includes/tls_params.conf	Parámetros TLS
ops/nginx/certs/	Certificados SSL/TLS

▶ Cómo levantar PRODUCCIÓN
Apagar DEV si está activo:

bash
Copiar código
docker compose -f docker-compose.dev.yml down
Marcar modo PROD (si usas switch-env.ps1):

powershell
Copiar código
.\switch-env.ps1 prod
Levantar producción:

bash
Copiar código
docker compose -f docker-compose.prod.yml up -d --build
🌍 Cómo probar PRODUCCIÓN
Servicio	URL
Proxy HTTP	http://localhost:8080
HTTPS (si activado)	https://localhost o tu dominio
Backend (proxy)	http://localhost:8080/api
Rasa (proxy)	http://localhost:8080/rasa
Health Nginx	http://localhost:8080/ping

⏹ Apagar PRODUCCIÓN
bash
Copiar código
docker compose -f docker-compose.prod.yml down
Si quieres limpiar también volúmenes (mucho cuidado en SERVIDORES reales):

bash
Copiar código
docker compose -f docker-compose.prod.yml down -v
🧹 Limpieza general de Docker
Eliminar contenedores, imágenes y redes no usadas:

bash
Copiar código
docker system prune -a
Eliminar solo redes huérfanas:

bash
Copiar código
docker network prune
Eliminar volúmenes no usados:

bash
Copiar código
docker volume prune
🔍 Problemas frecuentes
❌ “port already allocated 8000 / 8080 / 5005”
Otro proceso o contenedor está usando el puerto.

Pasos:

bash
Copiar código
docker ps
Detén el contenedor que esté ocupando el puerto:

bash
Copiar código
docker stop <nombre_o_id>
o ajusta el mapeo en docker-compose.dev.yml / docker-compose.prod.yml, por ejemplo:

yaml
Copiar código
ports:
  - "8002:8000"
❌ Red en uso: “resource is still in use”
Quedan contenedores unidos a la red.

Ver la red (ejemplo: app-net):

bash
Copiar código
docker network inspect app-net
Detener y borrar contenedores asociados:

bash
Copiar código
docker stop <nombres>
docker rm <nombres>
Eliminar la red:

bash
Copiar código
docker network rm app-net
🎯 Recomendación final
Usa DEV solo para desarrollo local, hot-reload y pruebas internas.

Usa PROD solo para simular el entorno completo de despliegue (local/VPS).

Mantén Nginx organizado:

conf.d/dev/default.conf → desarrollo

conf.d/prod/default.conf → HTTP producción

conf.d/prod/prod-https.conf → HTTPS listo para activarse con certificados válidos

Documenta siempre qué .env se usaron en cada despliegue (DEV/PROD)
para poder reproducir y auditar configuraciones en el Informe Técnico.

## 🧩 Entorno / perfil **VANILLA** (implementado pero no usado en la entrega)

El proyecto conserva un **perfil Docker “vanilla”** heredado de versiones anteriores.  
Este perfil está **implementado a nivel técnico**, pero:

- **No se utiliza ni se levanta** en la demostración oficial del proyecto.
- **No forma parte de las pruebas ni evidencias** incluidas en la entrega.
- Se deja únicamente como **entorno de laboratorio / diagnóstico** para futuros mantenedores.

Su objetivo es disponer de un entorno mínimo con los servicios esenciales del chatbot, usando imágenes preconstruidas, sin Nginx avanzado ni panel administrativo.

> 🔒 **Alcance académico**  
> El uso del perfil `vanilla` después de la entrega queda bajo responsabilidad de la institución que lo habilite.  
> En el contexto de este proyecto formativo, la operación en producción y el manejo de datos reales son responsabilidad del SENA si decide adoptarlo institucionalmente.

---

### 1️⃣ Características del entorno VANILLA

- Usa el perfil Docker: `vanilla` (definido en `docker-compose.yml` histórico).
- Servicios típicos:
  - `backend` (FastAPI)
  - `rasa` (motor conversacional)
  - `action-server` (acciones personalizadas de Rasa)
  - `mongo` (base de datos)
  - `redis` (si está definido)
- Normalmente **no incluye**:
  - Nginx de reverse proxy “completo” para embed.
  - Panel administrativo React / Vite.
- Es útil para:
  - Diagnosticar errores de modelo Rasa o backend.
  - Hacer pruebas puntuales de la API sin toda la infraestructura PROD/DEV.
  - Levantar rápido un entorno de prueba en máquina local.

---

### 2️⃣ Cuándo usar (y cuándo NO)

✅ **Casos en que puede ser útil:**

- Probar cambios en Rasa o el Action Server sin tocar la configuración de Nginx.
- Revisar conectividad básica entre servicios internos: backend ↔ Rasa ↔ Mongo.
- Hacer pruebas técnicas de laboratorio en un entorno aislado.

❌ **No recomendable para:**

- Demostraciones formales del proyecto.
- Escenarios de producción o pruebas con datos reales de aprendices.
- Validar la integración embebida en Zajuna (para eso se recomienda el stack completo PROD con Nginx).

En la memoria del proyecto y en el informe técnico, el entorno **oficialmente evaluado** es:

- **DEV**: `docker-compose.dev.yml`
- **PROD**: `docker-compose.prod.yml` (con Nginx y soporte para embed)

El perfil **`vanilla` queda documentado como opción técnica adicional, no evaluada.**

---

### 3️⃣ Cómo activar el perfil VANILLA

> ⚠️ Antes de usar este perfil, asegúrate de:
> - Tener `docker-compose.yml` con el perfil `vanilla` aún definido.
> - Haber detenido cualquier otro stack (`dev` o `prod`) para evitar conflictos de puertos.

#### 3.1. Levantar todo el entorno VANILLA

```bash
# Desde la raíz del proyecto
docker compose --profile vanilla up -d
--profile vanilla → indica a Docker que use únicamente los servicios marcados con ese perfil.

-d → levanta los contenedores en segundo plano.

Para reconstruir desde cero:

bash
Copiar código
docker compose --profile vanilla up -d --build
3.2. Levantar servicios individuales (vanilla)
Ejemplos (si tu docker-compose.yml los tiene bajo el perfil vanilla):

bash
Copiar código
# Solo backend
docker compose --profile vanilla up -d backend

# Solo Rasa
docker compose --profile vanilla up -d rasa

# Solo Action Server
docker compose --profile vanilla up -d action-server
4️⃣ Accesos típicos en modo VANILLA
Los puertos reales dependen de cómo estén mapeados en tu docker-compose.yml.
A modo de referencia típico:

Servicio	URL de ejemplo
Backend (FastAPI)	http://localhost:8000/docs
Endpoint de chat REST	http://localhost:8000/api/chat
Rasa HTTP API	http://localhost:5005
Rasa status	http://localhost:5005/status
Action Server (health)	http://localhost:5055/health (si está implementado)

En el contexto de embed en Zajuna, el perfil vanilla se podría usar para pruebas internas, pero:

No dispone normalmente del Nginx endurecido con CSP/CORS para iframe.

No es el entorno que se documenta como referencia para integración institucional.

Para integración real, se recomienda el entorno PROD con Nginx descrito en la propuesta embebida.

5️⃣ Logs, parada y limpieza (VANILLA)
5.1. Ver logs
bash
Copiar código
# Todos los servicios del perfil vanilla
docker compose --profile vanilla logs -f

# Solo backend
docker compose --profile vanilla logs -f backend

# Solo Rasa
docker compose --profile vanilla logs -f rasa
5.2. Apagar el entorno
bash
Copiar código
docker compose --profile vanilla down
5.3. Apagar y limpiar volúmenes (solo entorno de laboratorio)
⚠️ Esto borra datos de Mongo/Redis asociados a este perfil (no usar en entornos con datos que quieras conservar).

bash
Copiar código
docker compose --profile vanilla down -v
5.4. Reconstruir imágenes sin caché
bash
Copiar código
docker compose --profile vanilla build --no-cache