#!/bin/sh
set -eu

echo "Rasa entrypoint"

# =========================
# Config por variables ENV
# =========================
RASA_PORT="${RASA_PORT:-5005}"
RASA_HOST="${RASA_HOST:-0.0.0.0}"
RASA_CORS="${RASA_CORS:-*}"

# URL del Action Server
ACTION_SERVER_URL="${ACTION_SERVER_URL:-http://action-server:5055/webhook}"

# Plantilla de endpoints: default | mongo
ENDPOINTS_TEMPLATE="${ENDPOINTS_TEMPLATE:-default}"

# Si usas tracker en Mongo, predefine vars
if [ "$ENDPOINTS_TEMPLATE" = "mongo" ]; then
  TRACKER_MONGO_URL="${TRACKER_MONGO_URL:-mongodb://mongo:27017}"
  TRACKER_MONGO_DB="${TRACKER_MONGO_DB:-rasa}"
  TRACKER_MONGO_COLLECTION="${TRACKER_MONGO_COLLECTION:-conversations}"
fi

# =========================
# Render de endpoints.yml
# =========================
TPL="/app/endpoints.tpl.yml"
[ "$ENDPOINTS_TEMPLATE" = "mongo" ] && TPL="/app/endpoints.mongo.tpl.yml"

if [ -f "$TPL" ]; then
  echo "Renderizando /app/endpoints.yml desde $TPL"
  if command -v envsubst >/dev/null 2>&1; then
    envsubst < "$TPL" > /app/endpoints.yml
  else
    cp "$TPL" /app/endpoints.yml
    sed -i "s|\${ACTION_SERVER_URL}|$ACTION_SERVER_URL|g" /app/endpoints.yml || true
    if [ "$ENDPOINTS_TEMPLATE" = "mongo" ]; then
      sed -i \
        -e "s|\${TRACKER_MONGO_URL}|$TRACKER_MONGO_URL|g" \
        -e "s|\${TRACKER_MONGO_DB}|$TRACKER_MONGO_DB|g" \
        -e "s|\${TRACKER_MONGO_COLLECTION}|$TRACKER_MONGO_COLLECTION|g" \
        /app/endpoints.yml || true
    fi
  fi
else
  echo "No encontre plantilla $TPL. Usare /app/endpoints.yml si existe."
fi

echo "endpoints.yml resultante (si existe):"
( cat /app/endpoints.yml || true ) | sed -e 's/^/  /'

# =========================
# Entrenamiento (segun flags)
# =========================
mkdir -p /app/models

NEED_TRAIN=0
# Compat:
#  - RASA_AUTOTRAIN=true   -> entrena siempre
#  - RASA_FORCE_TRAIN=1    -> entrena siempre
if [ "${RASA_AUTOTRAIN:-false}" = "true" ] || [ "${RASA_FORCE_TRAIN:-0}" = "1" ]; then
  NEED_TRAIN=1
elif ! ls /app/models/*.tar.gz >/dev/null 2>&1; then
  NEED_TRAIN=1
fi

if [ "$NEED_TRAIN" -eq 1 ]; then
  echo "Entrenando modelo (rasa train)..."
  set +e
  rasa train \
    --domain /app/domain.yml \
    --data /app/data \
    --config /app/config.yml \
    --out /app/models \
    ${RASA_TRAIN_FLAGS:-}
  TRAIN_RC=$?
  set -e
  if [ $TRAIN_RC -ne 0 ]; then
    echo "Entrenamiento fallo (rc=$TRAIN_RC). Continuo sin detener el contenedor."
  fi
else
  echo "Modelo encontrado en /app/models. Omitiendo entrenamiento."
fi

# =========================
# Run server
# =========================
echo "Iniciando Rasa server en ${RASA_HOST}:${RASA_PORT} (CORS=${RASA_CORS})"
exec rasa run \
  --enable-api \
  -i "${RASA_HOST}" \
  -p "${RASA_PORT}" \
  --endpoints /app/endpoints.yml \
  --model /app/models \
  --cors "${RASA_CORS}"
