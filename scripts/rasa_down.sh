#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="${STATE_DIR:-.rasa}"
ACTIONS_PID_FILE="${STATE_DIR}/actions.pid"
RASA_PID_FILE="${STATE_DIR}/rasa.pid"

stop_pidfile () {
  local f="$1"
  local name="$2"
  if [[ -f "$f" ]]; then
    echo "ðŸ›‘ Deteniendo ${name}..."
    xargs -r kill < "$f" || true
    rm -f "$f"
  else
    echo "â„¹ï¸ ${name} no estaba corriendo (sin PID)."
  fi
}

stop_pidfile "$RASA_PID_FILE" "Rasa API"
stop_pidfile "$ACTIONS_PID_FILE" "Action Server"

echo "âœ… Todo detenido."
