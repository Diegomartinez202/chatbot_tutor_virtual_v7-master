#!/usr/bin/env bash
set -euo pipefail

# ===== Config por defecto (puedes sobreescribir por ENV) =====
RASA_DIR="${RASA_DIR:-rasa}"
RASA_PORT="${RASA_PORT:-5005}"
ACTIONS_PORT="${ACTIONS_PORT:-5055}"
STATE_DIR="${STATE_DIR:-.rasa}"
mkdir -p "${STATE_DIR}"

ACTIONS_PID_FILE="${STATE_DIR}/actions.pid"
RASA_PID_FILE="${STATE_DIR}/rasa.pid"

echo " Limpiando procesos previos (si existen)..."
if [[ -f "${ACTIONS_PID_FILE}" ]]; then
  xargs -r kill < "${ACTIONS_PID_FILE}" || true
  rm -f "${ACTIONS_PID_FILE}"
fi
if [[ -f "${RASA_PID_FILE}" ]]; then
  xargs -r kill < "${RASA_PID_FILE}" || true
  rm -f "${RASA_PID_FILE}"
fi

echo "ðŸ§  Validando & entrenando (opcional si ya entrenaste)..."
( cd "${RASA_DIR}" && rasa data validate && rasa train ) || true

echo "âš™ï¸  Iniciando Action Server en :${ACTIONS_PORT}..."
( cd "${RASA_DIR}" && rasa run actions -p "${ACTIONS_PORT}" ) \
  > "${STATE_DIR}/actions.log" 2>&1 &
echo $! > "${ACTIONS_PID_FILE}"

# Espera breve para que acciones arranquen
sleep 2

echo "ðŸš€ Iniciando Rasa HTTP API en :${RASA_PORT} (CORS abierto para pruebas)..."
( cd "${RASA_DIR}" && rasa run --enable-api -p "${RASA_PORT}" --cors "*" ) \
  > "${STATE_DIR}/rasa.log" 2>&1 &
echo $! > "${RASA_PID_FILE}"

echo "âœ… Listo:"
echo "â€¢ Actions   : http://localhost:${ACTIONS_PORT}/webhook"
echo "â€¢ Rasa API  : http://localhost:${RASA_PORT}"
echo "ðŸªµ Logs: ${STATE_DIR}/actions.log y ${STATE_DIR}/rasa.log"
