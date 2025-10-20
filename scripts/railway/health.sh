#!/usr/bin/env bash
set -euo pipefail

: "${BACKEND_URL:?BACKEND_URL no definido}"
: "${RASA_URL:?RASA_URL no definido}"
: "${ACTIONS_URL:?ACTIONS_URL no definido}"

have_jq() { command -v jq >/dev/null 2>&1; }
JQ=${JQ:-jq}
if ! have_jq; then
  JQ="cat"  # fallback si jq no está
fi

echo "== Backend =="
curl -fsSL "$BACKEND_URL/health" | $JQ
curl -fsSL "$BACKEND_URL/chat/health" | $JQ || true
if [ "${DEBUG:-false}" = "true" ]; then
  echo "-- /chat/debug --"
  curl -fsSL "$BACKEND_URL/chat/debug" | $JQ || true
fi

echo "== Rasa =="
curl -fsSL -X POST "$RASA_URL" -H "Content-Type: application/json" \
  -d '{"sender":"probe","message":"hola"}' | $JQ

echo "== Actions =="
# Si tu action server expone /health:
if curl -fsSL "$ACTIONS_URL/health" >/dev/null 2>&1; then
  curl -fsSL "$ACTIONS_URL/health" | $JQ
else
  echo "(sin /health, ok si 200 en /webhook)"
fi
