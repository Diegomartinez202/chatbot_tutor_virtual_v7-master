# ==========================================================
# Archivo : proxy_headers.inc
# Ubicación:
#   ops/nginx/conf.d/common/includes/proxy_headers.inc
#
# Propósito:
#   Centralizar los encabezados HTTP utilizados por todos los
#   proxy_pass del proyecto.
#
# Utilizado por:
#   - Frontend SPA
#   - Backend FastAPI
#   - Rasa
#   - Guardian
#   - Static
#   - Docs
#
# IMPORTANTE
# ----------
# Este archivo NO configura WebSocket.
# Las directivas:
#
#   proxy_set_header Upgrade ...
#   proxy_set_header Connection ...
#
# fueron separadas en:
#
#   websocket.inc
#
# para evitar enviar cabeceras Upgrade cuando no son necesarias.
# ==========================================================


# ----------------------------------------------------------
# Host original solicitado por el cliente
# ----------------------------------------------------------
proxy_set_header Host $host;


# ----------------------------------------------------------
# IP real del cliente
# ----------------------------------------------------------
proxy_set_header X-Real-IP $remote_addr;


# ----------------------------------------------------------
# Cadena completa de proxies
# ----------------------------------------------------------
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;


# ----------------------------------------------------------
# HTTP / HTTPS
# ----------------------------------------------------------
proxy_set_header X-Forwarded-Proto $scheme;


# ----------------------------------------------------------
# Host original (útil para FastAPI, OAuth y generación de URLs)
# ----------------------------------------------------------
proxy_set_header X-Forwarded-Host $host;


# ----------------------------------------------------------
# Puerto utilizado por el cliente
# ----------------------------------------------------------
proxy_set_header X-Forwarded-Port $server_port;