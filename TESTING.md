
✅ TESTING.md – Validación del Chatbot Embebido (FastAPI + Rasa)
0️⃣ Requisitos previos
🔧 Backend

FastAPI corriendo (modo DEV o PROD)

Variable DEBUG=true (solo durante pruebas) habilita /chat/debug.

🤖 Rasa

Rasa Core/API habilitado (--enable-api)

Action Server activo

🖼 Frontend (widget embebido)

VITE_ALLOWED_HOST_ORIGINS configurado para autorizar el dominio padre

Widget accesible en /static/widget/*

1️⃣ Variables requeridas (Frontend Vite)

Crea el archivo:

admin_panel_react/.env.local


Con:

VITE_ALLOWED_HOST_ORIGINS=https://app.zajuna.edu,http://localhost:5173
VITE_ZAJUNA_LOGIN_URL=https://zajuna.edu/login
VITE_CHAT_REST_URL=/api/chat


Importante:
El launcher compara orígenes estrictamente → el dominio del SPA y del iframe deben aparecer aquí.

2️⃣ Arranque local de todos los servicios
Backend
uvicorn backend.main:app --reload --port 8000

Rasa
rasa train
rasa run --enable-api -p 5005
rasa run actions -p 5055

Frontend (si se usa)
npm run dev

Docker (alternativa)
docker compose --profile dev up -d --build

3️⃣ Handshake de Autenticación (modo embebido)

En la página host (Zajuna / externa):

<script src="/chat-widget.js"
  data-chat-url="/chat-embed.html?embed=1"
  data-allowed-origins="https://app.zajuna.edu"
  data-login-url="https://app.zajuna.edu/login"
  data-badge="auto"></script>

<script>
  // Simulación de login local
  localStorage.setItem("zajuna_token", "JWT_DE_PRUEBA");
  window.getZajunaToken = () => localStorage.getItem("zajuna_token");
</script>

Flujo esperado

El iframe solicita contenido privado → envía auth:needed

El host responde con auth:token

Si no hay token → host redirige a login

Esto demuestra que el embed no expone la sesión del host, solo la puede solicitar vía postMessage (seguro).

4️⃣ Health Checks básicos
Local
curl http://localhost:8000/health | jq
curl http://localhost:8000/chat/health | jq
curl http://localhost:8000/chat/debug | jq       # DEBUG debe estar en true

Railway / Producción
export BACKEND_URL="https://<backend>.railway.app"
curl $BACKEND_URL/health | jq
curl $BACKEND_URL/chat/health | jq

5️⃣ Prueba rápida de /api/chat (smoke test)
🟥 Sin token (flujo público)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sender":"smoke","message":"hola","metadata":{}}' | jq

🟩 Con token (flujo privado)
TOKEN="<JWT_VALIDO>"

curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sender":"smoke","message":"/ver_certificados","metadata":{}}' | jq


En logs verás: rid=<ID> propagado hacia Rasa.

6️⃣ Verificación de X-Request-ID (trazabilidad completa)
A) cURL
curl -i -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sender":"ridtest","message":"hola"}'


En logs:

rid=1ac0d.... backend → rasa

B) Navegador

Abrir DevTools → Network

Mandar mensaje “hola”

Observar header:
X-Request-ID: <uuid>

7️⃣ Validación del Badge (contador) + postMessage
Simulación manual desde el iframe
Subir contador:
const parentOrigin = new URL(document.referrer).origin;
window.parent.postMessage({ type: "chat:badge", count: 5 }, parentOrigin);

Reset al abrir chat:
window.parent.postMessage({ type: "chat:visibility", open: true }, parentOrigin);

Configuración obligatoria

VITE_ALLOWED_HOST_ORIGINS debe contener el origin exacto del host.

8️⃣ Evidencias para el informe técnico

Recomendadas:

Pantalla completa del embedding (1440×900, zoom 100%)

/chat-embed con cards, replies y botones

Prueba de intent privado:

SIN token → “Iniciar sesión”

CON token → lista de certificados

Vista del badge incrementando → badge reseteado

9️⃣ Scripts Railway (opcionales)
export BACKEND_URL="https://<backend>.railway.app"
bash scripts/railway/health.sh
bash scripts/railway/smoke_chat.sh

🔥 10️⃣ Problemas comunes
❌ El badge no se actualiza

Revisa el postMessage en iframe

Verifica VITE_ALLOWED_HOST_ORIGINS

Verifica ev.origin del parent

❌ JWT inválido

Revisa SECRET_KEY o claves públicas

Revisa JWT_ALGORITHM

❌ No aparece X-Request-ID

Está en headers, no en body

El log lo muestra como rid=...

1️⃣1️⃣ Ubicación de archivos relevantes
Componente	Archivo
Widget principal	public/chat-widget.js
UI embebida	static/widget/*
Backend Chat	backend/app/api/chat.py
CSP / Embeds	backend/app/core/security/csp.py
Test E2E	tests/e2e/chat-embed.spec.ts
Scripts Railway	scripts/railway/