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

echo "[interactive] 🔎 Comprobando rutas requeridas..."
[ -f /app/config.yml ] || { echo "❌ Falta /app/config.yml"; exit 1; }
[ -d /app/data ] || { echo "❌ Falta /app/data"; exit 1; }
[ -d /app/domain_parts ] || { echo "❌ Falta /app/domain_parts"; exit 1; }

# 🧠 Combinar fragmentos del dominio en un único archivo antes de iniciar
echo "[interactive] ⚙️ Combinando fragmentos de dominio en /app/domain.yml..."
if rasa data convert domain --domain /app/domain_parts --out /app/domain.yml >/dev/null 2>&1; then
  echo "[interactive] ✅ Dominio combinado exitosamente: /app/domain.yml"
else
  echo "⚠️ No se pudo combinar el dominio automáticamente. Verifica los YAML en /app/domain_parts"
  exit 1
fi

# Carpeta para datos interactivos (montada en ./rasa/data/interactive en el host)
echo "[interactive] 📁 Asegurando carpeta /app/data/interactive ..."
mkdir -p /app/data/interactive

# Crear/asegurar archivos donde quieres ir guardando lo generado
: > /app/data/interactive/interactive_stories.yml
: > /app/data/interactive/interactive_nlu.yml
: > /app/data/interactive/interactive_rules.yml

# Entrena si no hay modelos, pero sin tumbar el contenedor si falla
if ! ls /app/models/*.tar.gz >/dev/null 2>&1; then
  echo "[interactive] 🛠️ No hay modelos entrenados. Validando + entrenando (best effort)..."
  rasa data validate \
    --domain /app/domain.yml \
    --data /app/data \
    --config /app/config.yml || true
  rasa train \
    --domain /app/domain.yml \
    --data /app/data \
    --config /app/config.yml || true
else
  echo "[interactive] 📦 Se encontraron modelos existentes. Saltando entrenamiento inicial."
fi

# Carpeta para logs/sesiones si la quieres usar luego
mkdir -p /app/interactive

# 🚀 Lanzar modo interactivo
echo "[interactive] 🚀 Iniciando Rasa Interactive..."
exec rasa interactive \
  --endpoints /app/endpoints.yml \
  --config /app/config.yml \
  --domain /app/domain.yml \
  --data /app/data \
  --model /app/models \
  --out /app/data/interactive \
  --port 5005 \
  --debug
