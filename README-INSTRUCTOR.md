
Indicaciones instructor para construir y levantar  containers en Docker compose:

Tutor Virtual Zajuna – Guía para el Instructor (Entorno Docker)

OJO: GitHub limita archivos individuales a 100 MB.
"Las imágenes Docker se encuentran en el ZIP entregado al instructor debido a limitación de GitHub."


Este proyecto contiene el **Tutor Virtual Zajuna** completamente contenerizado, listo para ser ejecutado con **Docker Compose** en modo desarrollo y producción.

Incluye:

- 🧠 **Rasa** (motor conversacional)
- ⚙️ **Action Server** (acciones personalizadas de Rasa)
- 🌐 **Backend FastAPI** (API central, logging, proxy hacia Rasa)
- 💻 **Panel administrativo React** (`admin-dev`)
- 🧩 **Servicio de embeddings**
- 🛡️ **Autosave Guardian**
- 🧠 **Ollama** (modelo LLM local: p.ej. `phi3:mini`)
- 🗄️ **MongoDB**
- ⚡ **Redis**
- 🔀 **Nginx** como proxy frontal (`nginx-dev`)

---

## 1. Requisitos previos

Antes de ejecutar el entorno, el instructor necesita:

- **Docker Desktop** (Windows/macOS) o **Docker Engine + Docker Compose** (Linux)
- Mínimo **8 GB de RAM** (recomendado 16 GB por el modelo LLM + Rasa)
- Al menos **20–25 GB de espacio en disco libre**
- Acceso a internet para:
  - Descargar imágenes Docker la primera vez
  - Permitir que **Ollama** descargue el modelo (por ejemplo `phi3:mini`)

---
## 2. Estructura del proyecto (carpeta principal)

La carpeta raíz del proyecto (la que viene en el ZIP o desde GitHub) tiene una estructura similar a:

chatbot_tutor_virtual_v7-master/
│
├── backend/
├── rasa/
├── admin-panel-react/
├── autosave-guardian/
├── embedding-service/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── Dockerfile (rasa, backend, etc.)
├── README.md
├── README-INSTRUCTOR.md
│
└── docker-images/ 
     ├── rasa.tar
     ├── backend.tar
     ├── action-server.tar
     ├── embedding-service.tar
     ├── autosave-guardian.tar
     ├── admin-dev.tar
     ├── ollama.tar
     ├── mongo.tar
     ├── redis.tar
     └── nginx.tar


Importante: en rasa/models/ se incluye el modelo entrenado
(por ejemplo: 20251210-031543-cool-parody.tar.gz)
que es el que se carga al iniciar el container rasa.

3. Configuración inicial
3.1. Obtener el código
Opción A – Desde ZIP

Descomprimir el ZIP entregado.

Entrar en la carpeta raíz del proyecto:
cd tutorbot-dev-full
Opción B – Desde GitHub
git clone <URL-DEL-REPOSITORIO>
cd tutorbot-dev-full
3.2. Variables de entorno
En la raíz del proyecto se incluye un archivo de ejemplo:
cp .env.example .env
Si desea, puede revisar .env, pero viene preconfigurado para
que el entorno dev funcione tal como se probó en la máquina del estudiante.

4. Ejecución en modo DESARROLLO
Este modo expone todos los servicios con los puertos que usa el estudiante en su entorno local, por ejemplo:

nginx-dev → http://localhost:8080

backend-dev → http://localhost:8000

rasa → http://localhost:5005

admin-dev → http://localhost:5173

mongo → puerto 27017

redis-dev → puerto interno 6379

ollama → http://localhost:11434

embedding-service → http://localhost:9000

autosave-guardian → http://localhost:8081

4.1. Construir e iniciar todos los containers (dev)
Desde la raíz del proyecto:
docker compose -f docker-compose.dev.yml up --build
Esto hará:

Construir las imágenes:

tutorbot-dev-full-backend-dev

tutorbot-dev-full-rasa

tutorbot-dev-full-action-server

tutorbot-dev-full-admin-dev

tutorbot-dev-full-embedding-service

tutorbot-dev-full-autosave-guardian

Levantar los servicios auxiliares:

mongo, redis-dev, nginx-dev, ollama

La primera vez puede tardar varios minutos (descarga de imágenes y modelo LLM).

Si ya prefiere ejecutar en segundo plano:

docker compose -f docker-compose.dev.yml up --build -d
5. Ejecución en modo PRODUCCIÓN 
Si desea probar una configuración más cercana a producción:

docker compose -f docker-compose.prod.yml up --build -d
Este archivo puede:

Usar configuración más estricta de logs

Deshabilitar hot-reload

Exponer solo los puertos necesarios (usualmente nginx y no los internos)

Para la evaluación del proyecto basta normalmente con docker-compose.dev.yml,
pero se incluye docker-compose.prod.yml para escenarios de despliegue.

6. Cómo probar que todo está funcionando
Una vez que todos los servicios estén arriba:

6.1. Chat del Tutor Virtual Zajuna
Abrir en el navegador:

http://localhost:8080/chat



Flujo mínimo de prueba:

Escribir HOLA.

Ver que responde algo como:

"¡Hola! Soy tu asistente Zajuna 👋
Este es el menú principal. ¿Qué deseas hacer?"

Probar el menú 🎓 Académico → “📚 Aprender un tema” → escribir un tema (ej. “desarrollo de software”).

6.2. Backend FastAPI (API central)
Abrir:

http://localhost:8000/docs
Ver la documentación Swagger de la API

Probar endpoints básicos como /api/health o /api/chat (según se haya configurado)

6.3. Rasa 
Verificar que el servidor Rasa está arriba:

curl http://localhost:5005/status

Debiera responder con un JSON indicando versión y modelo cargado.

7. Detener todo el entorno
Para detener los containers levantados con dev:

docker compose -f docker-compose.dev.yml down
Para detener producción:

docker compose -f docker-compose.prod.yml down

Si desea detener y además borrar volúmenes (ej. limpiar MongoDB):

docker compose -f docker-compose.dev.yml down -v

8. Notas sobre Ollama y el modelo LLM
El servicio ollama corre en el container ollama y expone el puerto 11434.

El modelo utilizado en este proyecto (phi3:mini) se descarga automáticamente
la primera vez que se llama desde el Action Server.

Si se quiere verificar a mano:

# Dentro de la máquina host
curl http://localhost:11434/api/tags

# O entrar al container ollama

docker exec -it ollama bash
ollama list

9. Resumen rápido para el instructor

Ir a la carpeta del proyecto:

cd tutorbot-dev-full
cp .env.example .env

Levantar entorno de desarrollo:

docker compose -f docker-compose.dev.yml up –build

Probar en el navegador:

Chat: http://localhost:8080/chat

API (Swagger): http://localhost:8000/docs

Detener el entorno al finalizar:

docker compose -f docker-compose.dev.yml down


# Paso rápido (sin descargar imágenes)
docker load -i tutorbot-imagenes.tar
docker compose -f docker-compose.dev.yml up

RESTORE DOCKER IMAGES

Para cargar las imágenes:

cd docker-images

docker load -i backend.tar
docker load -i rasa.tar
docker load -i action-server.tar
docker load -i admin.tar
docker load -i embedding.tar
docker load -i autosave-guardian.tar

docker load -i mongo.tar
docker load -i redis.tar
docker load -i nginx.tar
docker load -i ollama.tar


Luego ejecutar:

docker compose -f docker-compose.dev.yml up