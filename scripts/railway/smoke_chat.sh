#!/usr/bin/env bash
set -euo pipefail

: "${BACKEND_URL:?BACKEND_URL no definido}"

have_jq() { command -v jq >/dev/null 2>&1; }
JQ=${JQ:-jq}
if ! have_jq; then
  JQ="cat"
fi

echo "== Smoke /api/chat (SIN token) =="
curl -fsSL -X POST "$BACKEND_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"sender":"smoke","message":"/ver_certificados","metadata":{}}' | $JQ

if [ -n "${ACCESS_TOKEN:-}" ]; then
  echo "== Smoke /api/chat (CON token) =="
  curl -fsSL -X POST "$BACKEND_URL/api/chat" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"sender":"smoke","message":"/ver_certificados","metadata":{}}' | $JQ
else
  echo "(ACCESS_TOKEN no definido; se omite prueba con token)"
fi
