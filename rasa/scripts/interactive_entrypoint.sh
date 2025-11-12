#!/usr/bin/env sh
# POSIX: sin -o pipefail ni -E (propios de bash)
set -eu

echo "[interactive] 🧩 Escribiendo /app/endpoints.yml..."
cat > /app/endpoints.yml <<'YML'
action_endpoint:
  url: http://action-server:5055/webhook
tracker_store:
  type: rasa.core.tracker_store.MongoTrackerStore
  url: mongodb://mongo:27017
  db: rasa
  collection: conversations
YML

echo "[interactive] 🔎 Comprobando rutas..."
[ -f /app/config.yml ] || { echo "❌ Falta /app/config.yml"; exit 1; }
[ -d /app/data ] || { echo "❌ Falta /app/data"; exit 1; }
[ -d /app/domain_parts ] || { echo "❌ Falta /app/domain_parts"; exit 1; }

# Entrena si no hay modelos, pero sin tumbar el contenedor si falla
if ! ls /app/models/*.tar.gz >/dev/null 2>&1; then
  echo "[interactive] 🛠️ No hay modelos. Validando + entrenando (best effort)..."
  rasa data validate --domain /app/domain_parts --data /app/data --config /app/config.yml || true
  rasa train --domain /app/domain_parts --data /app/data --config /app/config.yml || true
fi

echo "[interactive] 🚀 Iniciando Rasa Interactive..."
mkdir -p /app/interactive
exec rasa interactive \
  --endpoints /app/endpoints.yml \
  --config /app/config.yml \
  --domain /app/domain_parts \
  --data /app/data \
  --model /app/models \
  --port 5005 \
  --debug
