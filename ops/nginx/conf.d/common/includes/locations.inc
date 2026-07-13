# ---- utilidades ----
location = /ping {
  add_header Content-Type text/plain;
  return 200 "ok\n";
}

# ========= Avatares =========
location = /user-avatar.png {
  try_files
      /embed/user-avatar.png
      /user-avatar.png
      /embed/bot-avatar.png
      /bot-avatar.png
      =404;
}

location = /mi-avatar.png   { try_files /mi-avatar.png =404; }
location = /bot-avatar.png  { try_files /embed/bot-avatar.png /bot-avatar.png =404; }
location = /bot-loading.png { try_files /embed/bot-loading.png /bot-loading.png =404; }


# ========= RASA vía /api/chat/rasa/*  =========
location ^~ /api/chat/rasa/ {
  proxy_pass         http://rasa_upstream/webhooks/;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header   Host              $host;
  proxy_set_header   X-Real-IP         $remote_addr;
  proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
  proxy_set_header   Upgrade           $http_upgrade;
  proxy_set_header   Connection        $connection_upgrade;

  client_max_body_size  25m;

  add_header 'Access-Control-Allow-Origin'      $http_origin    always;
  add_header 'Vary'                             'Origin'        always;
  add_header 'Access-Control-Allow-Credentials' 'true'          always;
  add_header 'Access-Control-Allow-Methods'     'GET,POST,PUT,PATCH,DELETE,OPTIONS' always;
  add_header 'Access-Control-Allow-Headers'     'Authorization,Content-Type,X-Requested-With' always;
  add_header 'Access-Control-Expose-Headers'    'Content-Length,Content-Type,X-Request-Id' always;
  if ($request_method = OPTIONS) { return 204; }

  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;

  proxy_buffering off;
}

# ========= API genérico → FastAPI =========
location /api/ {
  proxy_pass         http://backend_upstream;
  proxy_http_version 1.1;
  
  proxy_connect_timeout 10s;
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;
 
  proxy_set_header   Host              $host;
  proxy_set_header   X-Real-IP         $remote_addr;
  proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;

  proxy_set_header   Upgrade           $http_upgrade;
  proxy_set_header   Connection        $connection_upgrade;

  client_max_body_size  25m;

  add_header 'Access-Control-Allow-Origin'      $http_origin    always;
  add_header 'Vary'                             'Origin'        always;
  add_header 'Access-Control-Allow-Credentials' 'true'          always;
  add_header 'Access-Control-Allow-Methods'     'GET,POST,PUT,PATCH,DELETE,OPTIONS' always;
  add_header 'Access-Control-Allow-Headers'     'Authorization,Content-Type,X-Requested-With' always;
  add_header 'Access-Control-Expose-Headers'    'Content-Length,Content-Type,X-Request-Id' always;
  if ($request_method = OPTIONS) { return 204; }

  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;

  proxy_buffering off;
}

# ========= FRONTEND SPA =========
location / {

  add_header Content-Security-Policy
    "default-src 'self';
     img-src 'self' data: blob:;
     style-src 'self' 'unsafe-inline';
     script-src 'self' 'unsafe-eval';
     connect-src 'self' http: https: ws: wss:;
     frame-src 'self' *;
     frame-ancestors 'self'
     https://zajuna.sena.edu.co
     http://localhost:8080
     http://localhost:5173;"
    always;

  add_header Permissions-Policy
    "geolocation=(), microphone=(), camera=(), payment=(), autoplay=(), clipboard-write=()"
    always;

  add_header X-Frame-Options "SAMEORIGIN" always;

  proxy_pass http://admin_up;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout 300s;
  proxy_read_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;
  
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}

# ========= CHAT =========
location /chat/ {
  proxy_pass http://backend_upstream/chat/;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;


  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Host              $host;
  proxy_set_header X-Real-IP         $remote_addr;
  proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header Upgrade           $http_upgrade;
  proxy_set_header Connection        $connection_upgrade;
}

location = /chat         { add_header Cache-Control "no-cache, no-store, must-revalidate"; try_files /index.html =404; }
location = /chat-embed   { add_header Cache-Control "no-cache, no-store, must-revalidate"; try_files /index.html =404; }
location = /iframe/chat  { add_header Cache-Control "no-cache, no-store, must-revalidate"; try_files /index.html =404; }
location = /widget       { add_header Cache-Control "no-cache, no-store, must-revalidate"; try_files /index.html =404; }

location = /health {

  proxy_pass http://backend_upstream/health;

  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout 300s;
  proxy_read_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}
location = /auth/me     {

  proxy_pass http://backend_upstream/health;

  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout 300s;
  proxy_read_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}
location = /auth/logout {

  proxy_pass http://backend_upstream/health;

  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout 300s;
  proxy_read_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}

# ========= STATIC =========
location /static/ {
  proxy_pass         http://backend_upstream/static/;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header   Host $host;
  proxy_set_header   X-Real-IP $remote_addr;
  proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;
}

# ===============================
# Rasa HTTP API
# ===============================
location /rasa/ {

  proxy_pass http://rasa_upstream/;

  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection $connection_upgrade;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  proxy_buffering off;
  proxy_buffer_size 16k;
  proxy_buffers 8 16k;
  proxy_busy_buffers_size 32k;

  add_header Access-Control-Allow-Origin * always;
  add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
  add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

  if ($request_method = OPTIONS) {
      return 204;
  }
}

location = /rasa/status {

  proxy_pass http://rasa_upstream/status;

  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  add_header Access-Control-Allow-Origin "*" always;
}

location /ws/ {

  proxy_pass http://rasa_upstream/ws/;

  proxy_http_version 1.1;

  
  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection $connection_upgrade;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  proxy_buffering off;
}

# ========= Guardian =========
location /guardian/ {
  proxy_pass http://autosave-guardian:8080/;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_read_timeout 300s;
  proxy_send_timeout 300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;
  
  proxy_set_header Host              $host;
  proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Real-IP         $remote_addr;

  add_header Access-Control-Allow-Origin      $http_origin    always;
  add_header Vary                             Origin          always;
  add_header Access-Control-Allow-Credentials true            always;
  add_header Access-Control-Allow-Methods     "GET, POST, DELETE, OPTIONS" always;
  add_header Access-Control-Allow-Headers     "Authorization, Content-Type, Origin" always;

  if ($request_method = OPTIONS) { return 204; }

  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;

  proxy_buffering off;
}

# ========= Assets =========
location ~* \.(?:css|js|mjs|map|png|jpg|jpeg|gif|svg|ico|webp|woff2?|ttf|eot)$ {

  proxy_pass http://admin_up;
  proxy_http_version 1.1;
  
  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;


  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  expires 30d;
  add_header Cache-Control "public, max-age=2592000, immutable";
  access_log off;
}

location = /docs {
  proxy_pass         http://backend_upstream/docs;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header   Host $host;
  proxy_set_header   X-Real-IP $remote_addr;
  proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;
}

location = /docs/oauth2-redirect {
  proxy_pass http://backend_upstream/docs/oauth2-redirect;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;
}

location = /redoc {
  proxy_pass         http://backend_upstream/redoc;
  proxy_http_version 1.1;

  proxy_connect_timeout 10s;
  proxy_send_timeout    300s;
  proxy_read_timeout    300s;

  proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
  proxy_next_upstream_tries 5;
  proxy_next_upstream_timeout 60s;

  proxy_set_header   Host              $host;
  proxy_set_header   X-Real-IP         $remote_addr;
  proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
  proxy_hide_header Content-Security-Policy;
  proxy_hide_header Permissions-Policy;
}

location /embed/ {
  try_files $uri =404;
  expires 7d;
  add_header Cache-Control "public, max-age=604800";
}

location = /site.webmanifest {
  add_header Content-Type application/manifest+json;
  try_files /site.webmanifest =404;
}

location = /index.html {
  add_header Cache-Control "no-cache, no-store, must-revalidate";
  add_header Service-Worker-Allowed "/" always;
  try_files $uri =404;
}
location = /hybrid-host.html {
  add_header Cache-Control "no-cache, no-store, must-revalidate";
  add_header Service-Worker-Allowed "/" always;
  try_files /hybrid-host.html =404;
}
