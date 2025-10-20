# README.ops.md
# 🛠️ Guía técnica de operaciones (Paso a paso numerada)
Este documento contiene procedimientos paso a paso (numerados) para operaciones: despliegue en producción, backup/restore de MongoDB y Redis, rotación de logs, healthchecks, monitoreo y tareas de mantenimiento.

> Nota: los comandos asumen que usas `docker compose` (v2+) y los perfiles (`--profile prod`). Ajusta los nombres de servicio si en tu `docker-compose.yml` usas otros `container_name`.

---

## 0) Requisitos previos (antes de operar)
1. Acceso SSH al servidor donde corre Docker.
2. Docker Engine + Docker Compose v2 instalados.
3. Archivo `.env.prod` con credenciales (no versionado).
4. Tener espacio en disco para backups (ej. `/var/backups/tutorbot`).

---

## 1) Despliegue en producción (pasos)
1. **Subir variables de entorno seguras** (en servidor, fuera de Git):
   - Crear `/srv/tutorbot/.env.prod` o similar con los valores reales.
2. **Construir imágenes (si no provienen de registry)**:
   ```bash
   # En servidor (si construyes localmente)
   docker compose --profile prod build
Levantar el stack:

bash
Copiar código
docker compose --profile prod up -d
Verificar estado:

bash
Copiar código
docker compose --profile prod ps
docker compose --profile prod logs -f backend
Comprobar healthchecks básicos (ver sección Healthchecks).

2) Backup de MongoDB (paso a paso)
Usaremos mongodump. Si tu Mongo requiere autenticación, define MONGO_USER y MONGO_PASS.

2.1 Crear carpeta de backups (en host)
bash
Copiar código
mkdir -p /srv/tutorbot/backups/mongo
2.2 Backup (Bash)
Obtener container id:

bash
Copiar código
CONTAINER_ID=$(docker compose --profile prod ps -q mongo)
Ejecutar mongodump dentro del contenedor:

bash
Copiar código
docker exec -t $CONTAINER_ID mongodump --out /dump --gzip
Si requiere auth:

bash
Copiar código
docker exec -t $CONTAINER_ID mongodump --username "$MONGO_USER" --password "$MONGO_PASS" --authenticationDatabase admin --out /dump --gzip
Copiar el dump al host:

bash
Copiar código
docker cp $CONTAINER_ID:/dump /srv/tutorbot/backups/mongo/dump-$(date +%F)
(Opcional) Limpiar dump del contenedor:

bash
Copiar código
docker exec -t $CONTAINER_ID rm -rf /dump
2.3 Backup (PowerShell)
powershell
Copiar código
$cid = docker compose --profile prod ps -q mongo
docker exec -t $cid mongodump --out /dump --gzip
docker cp "$cid:/dump" "C:\ruta\backups\mongo\dump-$(Get-Date -Format yyyy-MM-dd)"
docker exec -t $cid rm -rf /dump
3) Restore de MongoDB (paso a paso)
Advertencia: restore sobreescribe datos. Haz backup antes.

3.1 Copiar backup al contenedor
bash
Copiar código
CONTAINER_ID=$(docker compose --profile prod ps -q mongo)
docker cp /srv/tutorbot/backups/mongo/dump-YYYY-MM-DD $CONTAINER_ID:/restore
3.2 Ejecutar mongorestore
bash
Copiar código
docker exec -t $CONTAINER_ID mongorestore --drop --gzip /restore
# Con auth:
docker exec -t $CONTAINER_ID mongorestore --username "$MONGO_USER" --password "$MONGO_PASS" --authenticationDatabase admin --drop --gzip /restore
3.3 Verificar
Conectar con mongosh y listar bases:

bash
Copiar código
docker exec -it $CONTAINER_ID mongosh --eval "db.adminCommand('listDatabases')"
4) Backup de Redis (paso a paso)
Redis usa dump.rdb por defecto (AOF si está configurado). Usamos SAVE.

4.1 Forzar snapshot y copiar
bash
Copiar código
CONTAINER_ID=$(docker compose --profile prod ps -q redis)
docker exec $CONTAINER_ID redis-cli SAVE
docker cp $CONTAINER_ID:/data/dump.rdb /srv/tutorbot/backups/redis/dump-$(date +%F).rdb
4.2 PowerShell (equivalente)
powershell
Copiar código
$cid = docker compose --profile prod ps -q redis
docker exec $cid redis-cli SAVE
docker cp "$cid:/data/dump.rdb" "C:\ruta\backups\redis\dump-$(Get-Date -Format yyyy-MM-dd).rdb"
5) Restore de Redis (paso a paso)
Advertencia: restaurar reemplaza la DB actual.

Copiar dump.rdb al contenedor:

bash
Copiar código
docker cp /srv/tutorbot/backups/redis/dump-YYYY-MM-DD.rdb $CONTAINER_ID:/data/dump.rdb
Reiniciar Redis:

bash
Copiar código
docker restart $CONTAINER_ID
Verificar:

bash
Copiar código
docker exec $CONTAINER_ID redis-cli PING
# Respuesta: PONG
6) Rotación de logs (paso a paso)
6.1 Preferible: usar opciones de logging en docker-compose.yml
Añade a servicios críticos:

yaml
Copiar código
logging:
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "7"
Luego reinicia servicio:

bash
Copiar código
docker compose --profile prod up -d backend
6.2 Opción host (logrotate) — pasos
Crear archivo /etc/logrotate.d/docker-containers con contenido:

bash
Copiar código
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
Probar manualmente:

bash
Copiar código
logrotate -d /etc/logrotate.d/docker-containers   # modo debug
logrotate /etc/logrotate.d/docker-containers      # ejecutar
7) Healthchecks y verificación (paso a paso)
7.1 Comprobar health via Docker
bash
Copiar código
docker compose --profile prod ps
# o estado específico:
docker inspect --format='{{json .State.Health}}' $(docker compose --profile prod ps -q backend)
7.2 Comprobaciones HTTP (ejemplos)
Backend:

bash
Copiar código
curl -fsS http://127.0.0.1:8000/chat/health || echo "backend DOWN"
Rasa:

bash
Copiar código
curl -fsS http://127.0.0.1:5005/status || echo "rasa DOWN"
Action Server:

bash
Copiar código
curl -fsS http://127.0.0.1:5055/ || echo "action-server DOWN"
8) Monitoreo rápido (docker stats / docker top) — paso a paso
Uso en tiempo real:

bash
Copiar código
docker compose --profile prod ps
docker compose --profile prod top backend
docker compose --profile prod stats
# Para limitar a un servicio:
docker stats $(docker compose --profile prod ps -q backend)
9) Actualización segura de imágenes (rolling update sencilla)
Hacer backup (Mongo/Redis) — ver pasos 2 y 4.

Pull de nuevas imágenes (si vienen del registry):

bash
Copiar código
docker compose --profile prod pull
Recrear contenedores uno a uno:

bash
Copiar código
docker compose --profile prod up -d backend
# Verificar logs y health
docker compose --profile prod logs -f backend
docker compose --profile prod ps
Repetir para otros servicios (rasa, action-server, admin).

Si construyes localmente:

bash
Copiar código
docker compose --profile prod build --no-cache
docker compose --profile prod up -d
10) Tareas programadas (cron) — Backup automático (ejemplo)
10.1 Script de backup básico ( /usr/local/bin/tutorbot_backup.sh )
bash
Copiar código
#!/bin/bash
# Directories
BACKUP_DIR=/srv/tutorbot/backups
DATE=$(date +%F)
mkdir -p $BACKUP_DIR/mongo $BACKUP_DIR/redis

# Mongo backup
CID=$(docker compose --profile prod ps -q mongo)
docker exec -t $CID mongodump --gzip --out /dump || exit 1
docker cp $CID:/dump $BACKUP_DIR/mongo/dump-$DATE
docker exec -t $CID rm -rf /dump

# Redis backup
CID_R=$(docker compose --profile prod ps -q redis)
docker exec $CID_R redis-cli SAVE
docker cp $CID_R:/data/dump.rdb $BACKUP_DIR/redis/dump-$DATE.rdb
Dar permisos y programar en crontab:

bash
Copiar código
chmod +x /usr/local/bin/tutorbot_backup.sh
# Edit crontab (ej. daily at 02:30)
30 2 * * * /usr/local/bin/tutorbot_backup.sh >> /var/log/tutorbot/backup.log 2>&1
11) Comprobaciones post-restore (validación)
Conectar al backend y probar endpoints críticos (login, chat, health).

Ejecutar consultas puntuales en Mongo para validar colecciones y conteos.

Ver logs por errores (stacktrace) tras el restore:

bash
Copiar código
docker compose --profile prod logs --since 10m
12) Checklist de seguridad antes de ir a producción
 .env.prod no está en el repo.

 Secretos almacenados en Vault / CI secrets o en host protegido.

 TLS activo en proxy (Nginx/Traefik) y certificados válidos.

 Backups automáticos habilitados y probados.

 Healthchecks configurados para servicios críticos.

 Rotación de logs configurada.

 Escaneo de imagen reciente (Trivy) antes del deploy.

 Restricciones de red (firewall) para puertos no públicos.

13) Comandos útiles rápidos (chuleta)
Levantar prod:

bash
Copiar código
docker compose --profile prod up -d
Logs backend:

bash
Copiar código
docker compose --profile prod logs -f backend
Stats:

bash
Copiar código
docker stats $(docker compose --profile prod ps -q backend)
Parar todo:

bash
Copiar código
docker compose --profile prod down
14) Advertencias y buenas prácticas finales
Nunca ejecutar restore en producción sin respaldo previo reciente.

Probar backup -> restore en staging regularmente.

Mantener backups fuera del mismo servidor (S3, GCP bucket) y cifrados.

Documentar rotación y retención (ej. conservar 30 días, comprimir) y probar recuperación.

Revisar permisos de archivos y ownership en backups exportados.

15) Contactos y escalado
Para incidentes graves: notificar al responsable de plataforma y abrir ticket en el sistema de incidentes con logs y dumps.

Mantener runbook con pasos resumidos para RTO/RPO.

✍️ Autor: Equipo Tutor Virtual
Fecha: (actualiza fecha en producción)

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
