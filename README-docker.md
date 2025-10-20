# 📦 Guía de Docker para Tutor Virtual

Este documento contiene todas las instrucciones necesarias para levantar los servicios del proyecto con **Docker Compose**, diferenciando entornos:

- **Vanilla** → Configuración mínima (sin perfiles).  
- **Build (dev)** → Desarrollo local con hot reload.  
- **Prod** → Producción con `.env.prod`.  

---

## 🔧 Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado.  
- [Docker Compose v2+](https://docs.docker.com/compose/) habilitado (`docker compose version`).  
- Variables de entorno configuradas:  
  - `.env.dev` (para desarrollo local)  
  - `.env.prod` (para producción)  
  - `.env.example` → plantilla de referencia  

---

## 🚀 Comandos por servicio

| Servicio       | Vanilla                               | Build (dev / hot reload)                        | Prod (producción)                          |
|----------------|---------------------------------------|------------------------------------------------|--------------------------------------------|
| **Backend**    | `docker compose up backend`           | `docker compose --profile build up backend`     | `docker compose --profile prod up backend` |
| **Admin**      | `docker compose up admin`             | `docker compose --profile build up admin`       | `docker compose --profile prod up admin`   |
| **Rasa**       | `docker compose up rasa`              | `docker compose --profile build up rasa`        | `docker compose --profile prod up rasa`    |
| **ActionSrv**  | `docker compose up action-server`     | `docker compose --profile build up action-server` | `docker compose --profile prod up action-server` |

---

## 🌐 Levantar todos los servicios

- **Vanilla (básico, sin perfiles):**
  ```bash
  docker compose up
Build (desarrollo local, hot reload):

bash
Copiar código
docker compose --profile build up
Producción (con .env.prod):

bash
Copiar código
docker compose --profile prod up -d
📂 Estructura de overrides
docker-compose.yml → base con servicios comunes.

docker-compose.override.yml → se activa solo en build para hot reload (montajes de código).

docker-compose.prod.yml (opcional) → configuración extendida de producción.

📜 Logs y monitoreo
Ver logs de un servicio:

bash
Copiar código
docker compose logs -f backend
Inspeccionar contenedor en ejecución:

bash
Copiar código
docker exec -it tutorbot-local-backend-1 sh
🧹 Limpieza
Detener y eliminar contenedores:

bash
Copiar código
docker compose down
Eliminar contenedores + volúmenes + redes:

bash
Copiar código
docker compose down -v
Reconstruir imágenes desde cero:

bash
Copiar código
docker compose build --no-cache
💡 Consejos
Usa perfiles para no mezclar entornos:

build → local/dev

prod → producción

Mantén los .env fuera de commits (.gitignore ya los excluye).

Para credenciales sensibles usa Docker secrets o variables en el host.

🔗 Diagrama de arquitectura (Mermaid)
mermaid
Copiar código
flowchart LR
    subgraph Frontend
        A[Admin Panel React] -->|HTTP| B(Backend FastAPI)
    end

    subgraph Backend
        B -->|REST/WS| C[Rasa]
        B -->|gRPC/REST| D[Action Server]
        B -->|MongoDB URI| E[(MongoDB)]
        B -->|Redis URL| F[(Redis)]
    end

    subgraph Infra
        E[(MongoDB)]
        F[(Redis)]
    end
📝 Chuleta rápida de atajos docker compose
Levantar todo

bash
Copiar código
docker compose up
Levantar con perfil build (dev/hot reload)

bash
Copiar código
docker compose --profile build up
Levantar en segundo plano (detached)

bash
Copiar código
docker compose up -d
Ver solo logs de backend

bash
Copiar código
docker compose logs -f backend
Reconstruir sin caché

bash
Copiar código
docker compose build --no-cache
Eliminar todo (contenedores + volúmenes + redes)

bash
Copiar código
docker compose down -v
✍️ Autor: Equipo Tutor Virtual
📌 Guía rápida para Docker y perfiles