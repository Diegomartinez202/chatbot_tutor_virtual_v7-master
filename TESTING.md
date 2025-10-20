TESTING – Zajuna (FastAPI + Rasa + Frontend)

Guía rápida para validar /api/chat, /chat, el X-Request-ID end-to-end y el badge del launcher/iframe.

✅ 0) Requisitos

Backend FastAPI corriendo y accesible.

Rasa (REST webhook y actions) corriendo y accesible.

DEBUG=true para habilitar /chat/debug (solo pruebas).

VITE_ALLOWED_HOST_ORIGINS configurado en el frontend (CSV) para validar postMessage.

🔧 1) Variables (frontend Vite)

Crea frontend/.env.local (o configura en Railway → Variables):

VITE_ALLOWED_HOST_ORIGINS=https://app.zajuna.edu,http://localhost:5173
VITE_ZAJUNA_LOGIN_URL=https://zajuna.edu/login
VITE_CHAT_REST_URL=/api/chat


Nota: el Badge y el launcher validan orígenes. Asegúrate de incluir el dominio del parent (panel) y del iframe si son distintos.

▶️ 2) Arranque local
# Backend FastAPI
uvicorn backend.main:app --reload --port 8000

# Rasa (en carpeta rasa/)
rasa train
rasa run --enable-api -p 5005
rasa run actions -p 5055

# Frontend (Vite)
npm run dev   # o: pnpm dev

🔐 3) Handshake de auth (embed)

En el host (página que inyecta el launcher):

<script src="/chat-widget.js"
  data-chat-url="/chat-embed.html?embed=1"
  data-allowed-origins="http://localhost:5173"
  data-login-url="http://localhost:5173/login"
  data-badge="auto"></script>

<script>
  // Simular login local:
  localStorage.setItem("zajuna_token", "JWT_DE_PRUEBA");
  window.getZajunaToken = () => localStorage.getItem("zajuna_token");
</script>


Flujo esperado:

El iframe requiere contenido privado → emite auth:needed.

El host responde con auth:token (si encuentra token) o redirige a login.

🩺 4) Health checks rápidos

Local

curl -sS http://localhost:8000/health | jq
curl -sS http://localhost:8000/chat/health | jq
curl -sS http://localhost:8000/chat/debug | jq   # requiere DEBUG=true


Railway

export BACKEND_URL="https://<backend>.railway.app"
curl -sS "$BACKEND_URL/health" | jq
curl -sS "$BACKEND_URL/chat/health" | jq
curl -sS "$BACKEND_URL/chat/debug" | jq   # si DEBUG=true

🚬 5) Smoke /api/chat (sin / con token)

SIN token → el backend fuerza metadata.auth.hasToken=false hacia Rasa

curl -sS -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sender":"smoke","message":"/ver_certificados","metadata":{}}' | jq


CON token → el backend fuerza metadata.auth.hasToken=true

TOKEN="<JWT_VALIDO>"
curl -sS -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer '"$TOKEN"'" \
  -H "Content-Type: application/json" \
  -d '{"sender":"smoke","message":"/ver_certificados","metadata":{}}' | jq


Tip: en ambos casos, revisa logs/system.log (o stdout en Railway) y busca rid=<X-Request-ID> para ver la correlación.

🆔 6) Verificación de X-Request-ID (end-to-end)

A) Desde cURL

curl -i -sS -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sender":"ridtest","message":"hola","metadata":{}}'


La respuesta no incluye el X-Request-ID en el body.

El header se propaga a Rasa y queda en logs.

Busca en logs:

tail -n 200 logs/system.log | grep rid=


B) Desde navegador (DevTools)

Abre tu SPA o /chat-embed.html.

En Network, envía un mensaje (p. ej. “hola”) y abre la request a /api/chat (o /chat).

En Request Headers verás: X-Request-ID: <uuid>.

Valida el mismo rid en logs/system.log.

🔔 7) Verificación del Badge (postMessage + orígenes)

A) Comportamiento esperado

En el Header (parent) usas: <Badge mode="chat" />.

El iframe (ChatUI) emite:

postMessage({ type: "chat:badge", count }, parentOrigin) → sube el contador.

El launcher (parent) emite hacia el iframe:

postMessage({ type: "chat:visibility", open: true }, frameOrigin) → el iframe resetea su contador; el Header también resetea su badge (Badge escucha el postMessage).

B) Simulación rápida (consola del iframe)

// ORIGEN del parent (ajústalo al del panel)
const parentOrigin = window.location !== window.parent.location
  ? (document.referrer && new URL(document.referrer).origin)
  : window.location.origin;

// Simula 5 sin leer
window.parent.postMessage({ type: "chat:badge", count: 5 }, parentOrigin);

// Simula apertura (reset)
window.parent.postMessage({ type: "chat:visibility", open: true }, parentOrigin);


C) Validación de orígenes

VITE_ALLOWED_HOST_ORIGINS debe incluir el origin del parent si difiere.

El launcher endurece targetOrigin al origin real del iframe y valida origin + source.

📸 8) Capturas para el informe

Tamaño: 1440×900, zoom 100%.

Planos: vista completa + detalle (cards/botones).

Rutas

/chat-embed (modo widget)

/chat (vista normal)

Secuencia

Carrusel de cursos (cards)
Mensaje: /explorar_temas → 3 cards (Excel, Soldadura, Web) + “Inscribirme”.

Recomendados
Tras /explorar_temas: “Python Básico – Ago 2025” y “IA Educativa – Sep 2025”.

Quick replies / sugerencias
Cualquier intent que devuelva quick_replies → chips horizontales.

Flujo privado (auth)

SIN token → /ver_certificados → “Iniciar sesión” (custom.type=auth_needed).

CON token → /ver_certificados → lista de certificados + botones.

🚂 9) Scripts Railway (opcional)
# Variables
export BACKEND_URL="https://<backend>.railway.app"
export RASA_URL="https://<rasa>.railway.app/webhooks/rest/webhook"
export ACTIONS_URL="https://<actions>.railway.app"
export DEBUG=true

# Health
bash scripts/railway/health.sh

# Smoke
bash scripts/railway/smoke_chat.sh   # ACCESS_TOKEN opcional

🧯 10) Problemas comunes

El badge no aparece

Verifica que el iframe emite postMessage (chat:badge).

Revisa VITE_ALLOWED_HOST_ORIGINS y que los orígenes coincidan (parent/iframe).

En el parent, loguea ev.origin y ev.data en el listener para depurar.

JWT inválido

Asegura JWT_ALGORITHM (HS vs RS) y claves (SECRET_KEY o JWT_PUBLIC_KEY).

El backend siempre fija metadata.auth.hasToken en base al Authorization real.

No veo X-Request-ID

No va en el body; está en headers hacia Rasa y en logs (rid=).

📁 11) Ubicación de archivos clave

Este documento: TESTING.md (raíz del repo).

Launcher: public/chat-widget.js (endurecido: frameOrigin + validación origin+source).

Chat embed UI: src/chat/ChatUI.jsx (emite chat:badge, escucha chat:visibility).

Badge unificado: src/components/Badge.jsx (<Badge mode="chat" /> en Header).

Header (SPA): src/components/Header.jsx (usa Badge y tooltips Radix).

Scripts Railway:

scripts/railway/health.sh

scripts/railway/smoke_chat.sh