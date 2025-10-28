# Bloques location comunes. NO define server{}.
# Requiere que el vhost que lo incluye defina:
#   upstream admin_up; upstream backend_up; upstream rasa_up;

# ===============================
# Frontend (admin)
# ===============================
location / {
  proxy_pass         http://admin_up;
  proxy_http_version 1.1;

  # WebSocket/HMR si aplica (Vite o similares)
  proxy_set_header Upgrade           $http_upgrade;
  proxy_set_header Connection        $connection_upgrade;

  proxy_set_header Host              $host;
  proxy_set_header X-Real-IP         $remote_addr;
  proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}

# ===============================
# API Backend (FastAPI)
# ===============================
location /api/ {
  # Preflight CORS simple (ajusta si quieres)
  if ($request_method = OPTIONS) {
    add_header Access-Control-Allow-Origin      $http_origin always;
    add_header Access-Control-Allow-Credentials "true" always;
    add_header Access-Control-Allow-Methods     "GET,POST,PUT,PATCH,DELETE,OPTIONS" always;
    add_header Access-Control-Allow-Headers     "Authorization,Content-Type,Accept,Origin,User-Agent" always;
    return 204;
  }
  add_header Access-Control-Allow-Origin      $http_origin always;
  add_header Access-Control-Allow-Credentials "true" always;

  proxy_pass         http://backend_up/;   # ← slash final para conservar subrutas
  proxy_http_version 1.1;

  proxy_set_header Upgrade           $http_upgrade;
  proxy_set_header Connection        "upgrade";
  proxy_set_header Host              $host;
  proxy_set_header X-Real-IP         $remote_addr;
  proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}

# ===============================
# Rasa HTTP API (bajo /rasa/)
# ===============================
location /rasa/ {
  proxy_pass         http://rasa_up/;   # ← SLASH FINAL
  proxy_http_version 1.1;

  proxy_set_header Upgrade           $http_upgrade;
  proxy_set_header Connection        "upgrade";
  proxy_set_header Host              $host;
  proxy_set_header X-Real-IP         $remote_addr;
  proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_buffering    off;

  # CORS básico (común)
  add_header Access-Control-Allow-Origin  * always;
  add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
  add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

  if ($request_method = OPTIONS) { return 204; }
}

# ===============================
# Salud directa de Rasa
# ===============================
location = /rasa/status {
  proxy_pass         http://rasa_up/status;
  proxy_http_version 1.1;
  proxy_set_header   Host $host;
  proxy_set_header   X-Real-IP $remote_addr;
  proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
  add_header Access-Control-Allow-Origin "*" always;
}

# ===============================
# Rasa WebSocket
# ===============================
location /ws/ {
  proxy_pass         http://rasa_up/ws/;  # ← slash final
  proxy_http_version 1.1;
  proxy_set_header   Upgrade $http_upgrade;
  proxy_set_header   Connection "upgrade";
  proxy_set_header   Host $host;
  proxy_set_header   X-Real-IP $remote_addr;
  proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
}
