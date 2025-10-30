#!/usr/bin/env bash
set -euo pipefail

# Variables Ãºtiles (puedes pasarlas desde docker-compose)
export ACTIONS_LOG_LEVEL="${ACTIONS_LOG_LEVEL:-INFO}"
export ACTIONS_LOG_FILE="${ACTIONS_LOG_FILE:-}"
export ACTIONS_MODULE="${ACTIONS_MODULE:-actions}"
export ACTIONS_PORT="${ACTIONS_PORT:-5055}"

echo "ðŸ§  Rasa Action Server"
echo "  â€¢ MODULE=${ACTIONS_MODULE}"
echo "  â€¢ PORT=${ACTIONS_PORT}"
echo "  â€¢ LOG_LEVEL=${ACTIONS_LOG_LEVEL}"
[ -n "${ACTIONS_LOG_FILE}" ] && echo "  â€¢ LOG_FILE=${ACTIONS_LOG_FILE}"

# Arranca el servidor de acciones
exec python -m rasa_sdk start \
  --actions "${ACTIONS_MODULE}" \
  --port "${ACTIONS_PORT}" \
  --logging-level "${ACTIONS_LOG_LEVEL}"
