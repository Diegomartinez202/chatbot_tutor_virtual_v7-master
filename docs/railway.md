# Despliegue en Railway (imágenes Docker Hub)

> ⚠️ **Estado actual**
>
> Este documento describe un posible despliegue en la plataforma Railway
> usando las imágenes Docker publicadas (`diego0102/zajuna-*`).
>
> En la entrega actual del proyecto:
> - **No se ha realizado ni verificado un despliegue real en Railway.**
> - El entorno soportado y probado es **Docker local** (dev/prod) con Nginx.
>
> Se deja este README como **guía de despliegue futuro** para quien quiera
> publicar el chatbot en la nube.

Prerrequisitos

Tener las imágenes publicadas en Docker Hub:

diego0102/zajuna-admin:latest

diego0102/zajuna-backend:latest

diego0102/zajuna-rasa:latest

diego0102/zajuna-action:latest

Variables en GitHub (para E2E):

PROD_FRONTEND_URL (URL pública del admin en Railway)

PROD_BACKEND_CHAT_BASE (URL pública del backend: https://tu-backend.railway.app/chat)

Arquitectura (servicios Railway)

admin (público): Nginx sirviendo el build de Vite.

backend (público): FastAPI.

rasa (privado): Core (puerto 5005) con API habilitada.

action-server (privado): rasa-sdk (puerto 5055).

mongo (plugin de Railway o cluster externo).

Descubrimiento de servicios (DNS interno Railway)

Cada servicio resuelve por su nombre:

backend → http://backend:8000

rasa → http://rasa:5005

action-server → http://action-server:5055

admin → http://admin:80

Usa exactamente esos hostnames en tus variables (ejemplo: RASA_URL=http://rasa:5005).

Crear proyecto y servicios

Crea un Project en Railway.

Agrega un servicio “New Service → Deploy from Image” para cada uno:

admin → image: docker.io/diego0102/zajuna-admin:latest

backend → image: docker.io/diego0102/zajuna-backend:latest

rasa → image: docker.io/diego0102/zajuna-rasa:latest

action-server → image: docker.io/diego0102/zajuna-action:latest

Agrega el plugin de MongoDB (o configura tu cluster externo).

Variables por servicio (mínimas)

backend:

APP_ENV=prod

DEBUG=false

MONGO_URI (desde el plugin)

MONGO_DB_NAME=tutor_virtual

SECRET_KEY (fuerte)

RASA_URL=http://rasa:5005

FRONTEND_SITE_URL=https://<tu-admin>.up.railway.app

ALLOWED_ORIGINS=https://<tu-admin>.up.railway.app,https://<tus-embeds>

rasa:

ACTION_SERVER_URL=http://action-server:5055/webhook

action-server:

Solo si tus actions requieren tokens/URLs.

admin:

Generalmente sin variables (estático).

Publicación (exponer servicios)

Marca admin y backend como “publicables”.

Deja rasa y action-server como privados (solo tráfico interno).

Health checks (recomendado)

backend: /health (200)

chat: /api/chat/health o /chat/health (200)

admin: / (200)

rasa: GET /status (si lo habilitas) o simplemente el puerto.

CSP y orígenes

Mantén en backend: frame-ancestors en headers para /chat-embed.html via FRONTEND_SITE_URL / EMBED_ALLOWED_ORIGINS.

En admin (Nginx) no necesitas CSP adicional salvo que quieras reforzarlo.

E2E en GitHub Actions

En el repo, agrega secrets:

PROD_FRONTEND_URL (URL del admin en Railway)

PROD_BACKEND_CHAT_BASE (https://…/chat)

Ejecuta el workflow “E2E Prod (Playwright)”.

Artefactos: playwright-report y test-results.

Redeploy desde GitHub

Usa el workflow deploy_railway.yml con RAILWAY_TOKEN y RAILWAY_PROJECT_ID.

O redeploy manual desde la UI de Railway.

Problemas comunes

CORS: añade todas las URLs del admin/embed en ALLOWED_ORIGINS del backend.

DNS interno: verifica que los nombres de servicio coincidan (rasa, action-server, backend).

SECRET_KEY débil: genera una fuerte (python -c "import secrets; print(secrets.token_urlsafe(64))").

502 en chat: revisa que RASA_URL apunte a http://rasa:5005 y ACTION_SERVER_URL esté correcto en rasa.

Checklist final

admin y backend “publicables”.

Variables del backend completas.

Imágenes en Docker Hub actualizadas (tag latest o específico).

E2E verdes contra PROD_FRONTEND_URL.