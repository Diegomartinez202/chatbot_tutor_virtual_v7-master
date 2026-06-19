---

# rasa/README.md

```md
# 🤖 Rasa Bot

Contiene `domain.yml`, `data/`, `config.yml`, plantillas de endpoints y Dockerfile. **No altera tu lógica**.

## 1) Endpoints / Tracker

Plantillas dentro de la imagen:
- `endpoints.tpl.yml` (**default**) → Action Server
- `endpoints.mongo.tpl.yml` → + Tracker en Mongo

Selecciona por ENV (en servicio `rasa` del compose):
```env
ACTION_SERVER_URL=http://action-server:5055/webhook
ENDPOINTS_TEMPLATE=default   # o "mongo"
# si usas mongo:
TRACKER_MONGO_URL=mongodb://mongo:27017
TRACKER_MONGO_DB=rasa
TRACKER_MONGO_COLLECTION=conversations
2) Entrenamiento
Auto-entrena si RASA_AUTOTRAIN=true o no hay modelos en /app/models.

Flags opcionales: RASA_TRAIN_FLAGS="--debug"

Manual dentro del contenedor:

bash
Copiar código
docker exec -it rasa sh
rasa train --domain /app/domain.yml --data /app/data --config /app/config.yml --out /app/models
3) Salud y REST
Status: GET http://localhost:5005/status
(vía Nginx: /rasa/status)

REST:

bash
Copiar código
curl -s http://localhost:5005/webhooks/rest/webhook \
  -H 'Content-Type: application/json' \
  -d '{"sender":"test","message":"hola"}'
Vía proxy:

bash
Copiar código
curl -s http://localhost/rasa/webhooks/rest/webhook \
  -H 'Content-Type: application/json' \
  -d '{"sender":"test","message":"hola"}'
4) Actions
Corren en contenedor aparte (action-server) con tu código de rasa/actions.

Variables útiles:

HELPDESK_WEBHOOK=http://backend:8000/api/helpdesk/tickets

ACTIONS_LOG_LEVEL=INFO

5) Modelos
Guardados en /app/models/*.tar.gz

GET /status muestra model_fingerprint activo.

6) Problemas comunes
actions 404 → revisa ACTION_SERVER_URL y que action-server esté UP.

Sin modelo → revisa logs de training; forzar RASA_FORCE_TRAIN=1.

Tracker en Mongo → usa ENDPOINTS_TEMPLATE=mongo + TRACKER_*.