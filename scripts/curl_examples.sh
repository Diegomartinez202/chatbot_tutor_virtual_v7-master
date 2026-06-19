#!/usr/bin/env bash
# scripts/curl_examples.sh
# Uso:
#   MODE=backend ./scripts/curl_examples.sh A        # Flujo soporte_form vÃ­a FastAPI (/api/chat)
#   MODE=rasa    ./scripts/curl_examples.sh A        # Flujo directo a Rasa REST
#   MODE=backend ./scripts/curl_examples.sh C0       # ver_certificados SIN token (utter_need_auth)
#   MODE=backend ./scripts/curl_examples.sh C1       # ver_certificados CON token (contenido real)
#   MODE=backend ./scripts/curl_examples.sh D0       # estado_estudiante SIN token
#   MODE=backend ./scripts/curl_examples.sh D1       # estado_estudiante CON token
#
# Env vars:
#   MODE=backend|rasa
#   BACKEND_CHAT (por defecto http://localhost:8000/api/chat)
#   RASA_REST    (por defecto http://localhost:5005/webhooks/rest/webhook)
#   TOKEN        (opcional) ejemplo: export TOKEN="Bearer eyJ..."
#
# Requiere: jq

set -euo pipefail

MODE="${MODE:-backend}"        # backend | rasa
SENDER_A="tester-001"
SENDER_B="tester-002"
SENDER_C="tester-003"
SENDER_D="tester-004"

# Endpoints
BACKEND_CHAT="${BACKEND_CHAT:-http://localhost:8000/api/chat}"          # FastAPI proxy
RASA_REST="${RASA_REST:-http://localhost:5005/webhooks/rest/webhook}"   # Rasa REST directo

# Auth opcional (si tu backend protege /api/chat)
TOKEN="${TOKEN:-}"   # export TOKEN="Bearer eyJ..."  (sin comillas si prefieres)

curl_json () {
  local url="$1"; shift
  local data="$1"; shift
  if [[ -n "${TOKEN}" ]]; then
    curl -sS -X POST "$url" -H "Content-Type: application/json" -H "Authorization: ${TOKEN}" -d "$data"
  else
    curl -sS -X POST "$url" -H "Content-Type: application/json" -d "$data"
  fi
}

# Construye y envÃ­a payloads SIEMPRE con metadata.auth.hasToken (true/false)
send_with_auth_flag () {
  local sender="$1"; shift
  local message="$1"; shift
  local hasToken="$1"; shift  # "true" o "false"
  local url payload

  if [[ "$MODE" == "backend" ]]; then
    url="$BACKEND_CHAT"
  else
    url="$RASA_REST"
  fi

  payload=$(jq -cn \
    --arg s "$sender" \
    --arg m "$message" \
    --argjson ht "$hasToken" \
    '{sender:$s, message:$m, metadata:{auth:{hasToken:$ht}, source:"curl"}}')

  curl_json "$url" "$payload"
}

# Igual que el anterior pero sin bandera explÃ­cita (para flows simples)
send () {
  local sender="$1"; shift
  local message="$1"; shift
  send_with_auth_flag "$sender" "$message" "false"
}

# ========== Flujos ==========
flow_A () {
  echo "== Flujo A: soporte_form =="
  send "$SENDER_A" "necesito soporte tÃ©cnico"; echo
  send "$SENDER_A" "Mi nombre es Daniel Martinez"; echo
  send "$SENDER_A" "daniel.martinez010201@gmail.com"; echo
  send "$SENDER_A" "Pantalla blanca al abrir el curso de IA."; echo
}

flow_B () {
  echo "== Flujo B: recovery_form =="
  send "$SENDER_B" "quiero ingresar a zajuna"; echo
  send "$SENDER_B" "recuperar contraseÃ±a"; echo
  send "$SENDER_B" "usuario+test@domain.io"; echo
}

# C: ver_certificados con/sin token
flow_C0 () {
  echo "== Flujo C0: /ver_certificados SIN token (debe pedir login) =="
  send_with_auth_flag "$SENDER_C" "/ver_certificados" "false" | jq .
}
flow_C1 () {
  echo "== Flujo C1: /ver_certificados CON token (debe dar contenido real) =="
  send_with_auth_flag "$SENDER_C" "/ver_certificados" "true" | jq .
}

# D: estado_estudiante con/sin token
flow_D0 () {
  echo "== Flujo D0: /estado_estudiante SIN token (debe pedir login) =="
  send_with_auth_flag "$SENDER_D" "/estado_estudiante" "false" | jq .
}
flow_D1 () {
  echo "== Flujo D1: /estado_estudiante CON token (debe dar contenido real) =="
  send_with_auth_flag "$SENDER_D" "/estado_estudiante" "true" | jq .
}

case "${1:-A}" in
  A) flow_A ;;
  B) flow_B ;;
  C0) flow_C0 ;;
  C1) flow_C1 ;;
  D0) flow_D0 ;;
  D1) flow_D1 ;;
  *)
    echo "Uso: $0 [A|B|C0|C1|D0|D1]"
    echo "  A = soporte_form"
    echo "  B = recovery_form"
    echo "  C0= ver_certificados SIN token"
    echo "  C1= ver_certificados CON token"
    echo "  D0= estado_estudiante SIN token"
    echo "  D1= estado_estudiante CON token"
    exit 1
    ;;
esac
