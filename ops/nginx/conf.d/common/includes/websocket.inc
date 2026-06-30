# ==========================================================
# WebSocket común
#
# Este archivo contiene únicamente la configuración común
# para conexiones WebSocket.
#
# NO define:
#   - proxy_pass
#   - proxy_set_header Host
#   - proxy_set_header X-Real-IP
#   - proxy_set_header X-Forwarded-*
#
# Esas directivas permanecen en cada location ya que pueden
# apuntar a distintos upstreams.
#
# Utilizar:
#
#     include conf.d/common/includes/websocket.inc;
#
# dentro de los location que soporten WebSocket.
# ==========================================================

# HTTP/1.1 requerido para WebSocket
proxy_http_version 1.1;

# Upgrade de conexión
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;

# Evitar buffering para tráfico bidireccional
proxy_buffering off;

# Timeouts suficientemente amplios
proxy_read_timeout 120s;
proxy_send_timeout 120s;