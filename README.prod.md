# 🚀 Guía de Despliegue en Producción (Tutor Virtual)

Este documento contiene las instrucciones específicas para desplegar el proyecto en **entorno de producción** usando Docker Compose.  
No incluye configuraciones de desarrollo ni perfiles de build.

---

## 🔧 Requisitos previos

- [Docker Engine](https://docs.docker.com/engine/) instalado en el servidor.  
- [Docker Compose v2+](https://docs.docker.com/compose/) habilitado (`docker compose version`).  
- Variables de entorno configuradas en el archivo **`.env.prod`** (basado en `.env.prod.example`).  

---

## 📂 Archivos clave

- `docker-compose.yml` → definición base de servicios.  
- `.env.prod` → configuración de entorno **real de producción** (no versionado).  

Opcionalmente puedes tener:  
- `docker-compose.prod.yml` → overrides específicos de producción (si lo requieres).  

---

## 🌐 Levantar todos los servicios en producción

Ejecutar en el servidor:

```bash
docker compose --profile prod up -d
--profile prod → selecciona el perfil de producción.

-d → levanta los contenedores en segundo plano (detached).

🚀 Levantar servicios individuales (prod)
Backend (FastAPI)

bash
Copiar código
docker compose --profile prod up -d backend
Admin Panel (React + Vite)

bash
Copiar código
docker compose --profile prod up -d admin
Rasa (NLP)

bash
Copiar código
docker compose --profile prod up -d rasa
Action Server (Rasa Actions)

bash
Copiar código
docker compose --profile prod up -d action-server
📜 Logs y monitoreo
Ver logs de todos los servicios:

bash
Copiar código
docker compose --profile prod logs -f
Ver solo logs de un servicio (ejemplo: backend):

bash
Copiar código
docker compose --profile prod logs -f backend
Inspeccionar un contenedor en ejecución:

bash
Copiar código
docker exec -it tutorbot-local-backend-1 sh
🧹 Mantenimiento y limpieza
Detener servicios:

bash
Copiar código
docker compose --profile prod down
Detener y eliminar contenedores + volúmenes:

bash
Copiar código
docker compose --profile prod down -v
Reconstruir imágenes desde cero:

bash
Copiar código
docker compose --profile prod build --no-cache
🔒 Seguridad y buenas prácticas
Nunca subir .env.prod a Git (ya está en .gitignore).

Rotar contraseñas y claves JWT regularmente.

Usar HTTPS en los dominios (BASE_URL, FRONTEND_SITE_URL).

Configurar monitoreo y backups en MongoDB y Redis.

Revisar que los puertos expuestos en producción sean solo los necesarios.

📝 Resumen rápido
bash
Copiar código
# 1. Configurar variables
cp .env.prod.example .env.prod

# 2. Construir imágenes
docker compose --profile prod build

# 3. Levantar en background
docker compose --profile prod up -d

# 4. Ver logs
docker compose --profile prod logs -f
✍️ Autor: Equipo Tutor Virtual
📌 Guía de despliegue en Producción