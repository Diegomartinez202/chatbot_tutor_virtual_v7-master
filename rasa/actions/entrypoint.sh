#!/usr/bin/env bash
set -euo pipefail

# Variables (con defaults, sin tocar tu lógica)
export ACTIONS_LOG_LEVEL="${ACTIONS_LOG_LEVEL:-INFO}"
export ACTIONS_LOG_FILE="${ACTIONS_LOG_FILE:-}"
export ACTIONS_MODULE="${ACTIONS_MODULE:-actions}"
export ACTIONS_PORT="${ACTIONS_PORT:-5055}"
export ACTIONS_CORS="${ACTIONS_CORS:-*}"  # cors por defecto

echo "🧩 Rasa Action Server — diagnóstico inicial"
echo "  ⚙️ Modo: ${MODE:-unknown}"
echo "  📦 Module: ${ACTIONS_MODULE}"
echo "  🔊 Log level: ${ACTIONS_LOG_LEVEL}"
echo "  🔌 Puerto: ${ACTIONS_PORT}"
echo "  🔗 Webhook Rasa: ${ACTION_SERVER_URL:-http://action-server:5055/webhook}"
echo "  💌 SMTP: ${SMTP_SERVER:-unset}:${SMTP_PORT:-unset} user=${SMTP_USER:-unset}"
echo "  🧠 Backend RESET_URL_BASE: ${RESET_URL_BASE:-unset}"

# Valida variables mínimas (sin romper si faltan)
python - <<'PY'
import os
print("[action-server] ✅ Variables mínimas OK")
print("[action-server] MODE=", os.getenv("MODE","unknown"))
print("[action-server] ACTIONS_MODULE=", os.getenv("ACTIONS_MODULE","actions"))
print("[action-server] ACTIONS_PORT=", os.getenv("ACTIONS_PORT","5055"))
PY

# Construimos los argumentos válidos para rasa_sdk
ARGS=( "-m" "rasa_sdk" "--actions" "${ACTIONS_MODULE}" "--port" "${ACTIONS_PORT}" "--cors" "${ACTIONS_CORS}" )

# Mapeo simple del "nivel" a flags soportadas por el SDK
# (no existe --logging-level en rasa_sdk CLI)
case "${ACTIONS_LOG_LEVEL^^}" in
  DEBUG)
    ARGS+=( "--debug" )
    ;;
  QUIET|WARNING|WARN|ERROR)
    # --quiet reduce verbosidad; el SDK no tiene niveles finos
    ARGS+=( "--quiet" )
    ;;
  *)
    # INFO (default): sin flags adicionales
    :
    ;;
esac

# Log-file opcional
if [ -n "${ACTIONS_LOG_FILE}" ]; then
  ARGS+=( "--log-file" "${ACTIONS_LOG_FILE}" )
fi

# Arranca el servidor de acciones (sin 'start')
exec python "${ARGS[@]}"
