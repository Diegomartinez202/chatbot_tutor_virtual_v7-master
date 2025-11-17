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

# --------------------------------------------------------------------
# 🧠 DOMINIO: híbrido
# 1) Si existe /app/domain_parts con YAML → fusiona en /app/domain.yml
# 2) Si no, usa /app/domain.yml centralizado
# --------------------------------------------------------------------

DOMAIN_FILE="/app/domain.yml"

if [ -d /app/domain_parts ] && ls /app/domain_parts/*.yml >/dev/null 2>&1; then
  echo "[interactive] ⚙️ Se encontró carpeta /app/domain_parts con YAML."
  echo "[interactive] 🔧 Combinando fragmentos del dominio en ${DOMAIN_FILE}..."

  if rasa data convert domain --domain /app/domain_parts --out "${DOMAIN_FILE}" >/dev/null 2>&1; then
    echo "[interactive] ✅ Dominio combinado exitosamente: ${DOMAIN_FILE}"
  else
    echo "⚠️ Error combinando dominio desde /app/domain_parts. Revisa los YAML."
    exit 1
  fi
else
  echo "[interactive] 📄 Usando dominio centralizado: ${DOMAIN_FILE}"
  [ -f "${DOMAIN_FILE}" ] || { echo "❌ No existe dominio centralizado en ${DOMAIN_FILE}"; exit 1; }
fi

# --------------------------------------------------------------------
# 🗂  CREAR CARPETA DE SESIÓN INTERACTIVA + ARCHIVOS
# --------------------------------------------------------------------

echo "[interactive] 📁 Asegurando carpeta raíz /app/data/interactive ..."
mkdir -p /app/data/interactive

SESSION_ID="$(date +'%Y%m%d_%H%M%S')"
INTERACTIVE_DIR="/app/data/interactive/session_${SESSION_ID}"

echo "[interactive] 🗂  Creando carpeta de sesión: ${INTERACTIVE_DIR}"
mkdir -p "${INTERACTIVE_DIR}"

NLU_FILE="${INTERACTIVE_DIR}/nlu.yml"
STORIES_FILE="${INTERACTIVE_DIR}/stories.yml"
RULES_FILE="${INTERACTIVE_DIR}/rules.yml"

# Crear archivos vacíos (si no existen) con encabezado mínimo
init_nlu() {
  if [ ! -f "${NLU_FILE}" ]; then
    echo "[interactive] ✍️ Inicializando ${NLU_FILE}"
    cat > "${NLU_FILE}" <<EOF
version: "3.1"

nlu:
  # ejemplos generados en modo interactivo
EOF
  fi
}

init_stories() {
  if [ ! -f "${STORIES_FILE}" ]; then
    echo "[interactive] ✍️ Inicializando ${STORIES_FILE}"
    cat > "${STORIES_FILE}" <<EOF
version: "3.1"

stories:
  # historias generadas en modo interactivo
EOF
  fi
}

init_rules() {
  if [ ! -f "${RULES_FILE}" ]; then
    echo "[interactive] ✍️ Inicializando ${RULES_FILE}"
    cat > "${RULES_FILE}" <<EOF
version: "3.1"

rules:
  # reglas generadas en modo interactivo
EOF
  fi
}

init_nlu
init_stories
init_rules

echo "[interactive] 💾 Los datos interactivos de esta sesión se guardarán en:"
echo "   NLU     : ${NLU_FILE}"
echo "   Stories : ${STORIES_FILE}"
echo "   Rules   : ${RULES_FILE}"
echo "   Carpeta : ${INTERACTIVE_DIR}"

# --------------------------------------------------------------------
# 📦 ENTRENAMIENTO PREVIO (SOLO SI NO HAY MODELOS)
# --------------------------------------------------------------------

if ! ls /app/models/*.tar.gz >/dev/null 2>&1; then
  echo "[interactive] 🛠️ No hay modelos entrenados. Validando + entrenando..."
  rasa data validate \
    --domain "${DOMAIN_FILE}" \
    --data /app/data \
    --config /app/config.yml || true

  rasa train \
    --domain "${DOMAIN_FILE}" \
    --data /app/data \
    --config /app/config.yml || true
else
  echo "[interactive] 📦 Se encontraron modelos existentes. Saltando entrenamiento inicial."
fi

# --------------------------------------------------------------------
# 🚀 INICIAR SESIÓN INTERACTIVA
# --------------------------------------------------------------------

echo "[interactive] 🚀 Iniciando Rasa Interactive..."
exec rasa interactive \
  --endpoints /app/endpoints.yml \
  --config /app/config.yml \
  --domain "${DOMAIN_FILE}" \
  --data /app/data \
  --model /app/models \
  --nlu "${NLU_FILE}" \
  --stories "${STORIES_FILE}" \
  --rules "${RULES_FILE}" \
  --out "${INTERACTIVE_DIR}" \
  --port 5005 \
  --debug
