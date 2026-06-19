📘 README — Implementación Embebida del Chatbot Tutor Virtual en Zajuna

Versión institucional — Proyecto SENA

Este documento describe cómo integrar el Chatbot Tutor Virtual como widget embebido dentro de Zajuna (u otros portales institucionales), sin modificar su código fuente, garantizando aislamiento, seguridad, trazabilidad y compatibilidad con entornos DEV / PROD / VANILLA.

🔒 Nota institucional (alcance de entrega)
El panel administrativo en React/Vite NO será desplegado ni evaluado en esta entrega, por razones de alcance, seguridad y autorización institucional.
El chatbot funciona 100% sin panel: backend FastAPI + Rasa + MongoDB + widget embebido.

⚠️ Responsabilidad sobre datos
Después de la entrega del proyecto, el SENA es el responsable único del uso, tratamiento y almacenamiento de datos si decide poner el sistema en operación real, según lineamientos institucionales.

🧩 1. Objetivo del README

Este archivo explica:

✔ Cómo integrar el chatbot mediante script launcher o iframe
✔ Cómo funciona el widget embebible
✔ Configuración de CSP / CORS / seguridad
✔ Variables de entorno necesarias
✔ Funcionamiento del postMessage
✔ El rol de DEV, PROD y VANILLA
✔ Pruebas, smoke-tests y troubleshooting

🏗️ 2. Arquitectura de Integración

El chatbot NO se inserta directamente en Zajuna.
El sistema usa un launcher JavaScript + iframe aislado, garantizando:

Aislamiento visual

Aislamiento de estilos

No colisión de JS

Seguridad CSP/iframe sandbox

Fácil actualización sin tocar Zajuna

Comunicación segura vía postMessage

Zajuna
  └── Script launcher (chat-widget.js)
         └── Panel → iframe
                   └── chat-embed.html
                           └── /chat → backend → Rasa

📁 3. Archivos que se deben publicar

Dentro del servidor estático del frontend (Nginx o CDN):

/static/
   chat-widget.js        ← script principal (launcher)
/static/chat-embed.html ← wrapper del iframe
/static/bot-avatar.png
/static/site.webmanifest


Zajuna solo incluye un <script> y eso basta.

🔧 4. Variables de Entorno Necesarias
🔹 Frontend (React/Vite)

Estas variables controlan el transporte REST/WS del chat:

VITE_CHAT_TRANSPORT=rest
VITE_CHAT_REST_URL=/api/chat
VITE_RASA_WS_URL=wss://TU_DOMINIO/rasa
VITE_ALLOWED_HOST_ORIGINS=https://zajuna.sena.edu.co

🔹 Backend (FastAPI)

CORS + CSP:

APP_ENV=prod
ALLOWED_ORIGINS=https://app.zajuna.edu,https://zajuna.sena.edu.co
FRAME_ANCESTORS=https://zajuna.sena.edu.co https://*.zajuna.sena.edu.co
CHAT_REQUIRE_AUTH=false     # embebido anónimo (por ahora)
DEMO_MODE=false

💬 5. Snippet Oficial para Integrar en Zajuna
🔹 Opción A — Script Launcher (recomendada)

Pegar en la página principal o en la plantilla HTML de Zajuna:

<script
  src="https://TU_DOMINIO/static/chat-widget.js"
  data-chat-url="/static/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px"
  data-avatar="/static/bot-avatar.png"
  data-title="Chat Tutor Virtual"
  data-position="bottom-right"
  data-panel-width="380px"
  data-panel-height="560px"
  data-allowed-origins="https://zajuna.sena.edu.co,https://app.zajuna.edu"
  data-login-url=""
  data-badge="auto"
  data-version="1.0.0"
  defer
></script>


✔ No interfiere con Zajuna
✔ Auto inicializable
✔ Badge dinámico
✔ Seguro mediante whitelist de orígenes

🔹 Opción B — Iframe directo (menos completa)
<iframe
  src="/static/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px"
  width="380"
  height="560"
  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  style="border:0;border-radius:16px;overflow:hidden"
></iframe>

🔐 6. Seguridad: CORS / CSP / SANDBOX
CORS Backend
add_header Access-Control-Allow-Origin https://zajuna.sena.edu.co;
add_header Access-Control-Allow-Credentials true;

CSP en Nginx

Evita que Zajuna incruste orígenes no autorizados:

frame-ancestors https://zajuna.sena.edu.co https://*.zajuna.sena.edu.co;

iframe sandbox

Protección obligatoria:

allow-scripts allow-forms allow-same-origin allow-popups

🔄 7. Comunicación Segura (postMessage)

Eventos soportados:

Evento	Sentido	Uso
chat:ready	iframe → host	Notifica carga
chat:settings	host → iframe	Tema/idioma/contraste
chat:visibility	host → iframe	Abrir/cerrar
chat:badge	iframe → host	No leídos

Todos los mensajes incluyen v: "1" para versionado.

🚀 8. Perfiles Docker para Integración

El proyecto implementa 3 perfiles:

🔹 1. DEV

Para desarrollo local (hot reload).

docker compose --profile build up -d --build

🔹 2. PROD

Para despliegue real detrás de Nginx.

docker compose --profile prod up -d --build

🔹 3. VANILLA (laboratorio)

🔸 Perfil implementado pero NO usado oficialmente.
Sirve para:

pruebas de laboratorio,

ejecutar imágenes preconstruidas,

ver si hay problemas con versiones previas,

validar infraestructura mínima sin frontend ni override.

Se activa así:

docker compose --profile vanilla up -d


Incluye:

Servicio	Estado en VANILLA
backend	Sí, imagen remota
rasa	Sí
action	Sí
admin	❌ No (fuera de alcance)
nginx	Opcional (según override)

Justificación por documentación:

Permite pruebas rápidas sin build local.

Útil para validación CI/CD (Railway).

No recomendado para producción.

🧪 9. Smoke Tests
1️⃣ Probar chat directo
http://localhost/chat

2️⃣ Probar embed
http://localhost/static/chat-embed.html?src=/chat%3Fembed%3D1

3️⃣ Probar launcher en HTML de prueba

Copiar snippet en una página local.

4️⃣ Probar WebSocket
wscat -c ws://localhost/ws

🧹 10. Troubleshooting
❌ El widget no abre

→ Revisar data-allowed-origins.

❌ El iframe no carga

→ Revisar FRAME_ANCESTORS.

❌ 401 en /api/chat

→ CHAT_REQUIRE_AUTH debe ser false (modo embed).

❌ WS no conecta

→ Revisar configuración de Upgrade/Connection en Nginx.

📦 11. Repositorio — Estructura Relevante del Widget
public/
 ├─ chat-widget.js
 ├─ chat-embed.html
 ├─ bot-avatar.png
 ├─ site.webmanifest


Backend:

backend/
 ├─ main.py
 ├─ routers/chat.py
 └─ core/security.py

🏁 12. Conclusión del README

La integración propuesta permite que el Chatbot Tutor Virtual funcione dentro de Zajuna:

sin modificar su código,

con seguridad institucional,

con aislamiento total,

con transporte REST/WS,

con trazabilidad y telemetría,

con compatibilidad hacia un futuro SSO.

Es una solución sencilla de montar, segura y totalmente escalable.


🔒 Garantía de seguridad y pruebas aplicadas para integración embebida (Zajuna + Híbrido)

La integración embebida del Chatbot Tutor Virtual ha sido validada con pruebas orientadas exclusivamente a su comportamiento como:

widget seguro,

aislado,

con headers CSP explícitos,

y compatible con sistemas externos como Zajuna.

🟩 Pruebas relevantes para el modo embebido
Test	Rol en la Integración
test_embed_redirects.py	Asegura que el embed no permita navegación fuera del contenedor
test_csp_headers.py	Verifica políticas CSP para prevenir inyección o acceso indebido
test_chat_proxy.py (si aplica)	Confirma el puente seguro entre iframe/script → backend
test_chat.py	Mensajes enviados y recibidos correctamente desde el widget
test_functional_flow.py	Flujo completo del usuario dentro de un entorno embebido
test_static_mount.py	Widget disponible vía /static/widget/*.js
🟧 Tests NO incluidos (no aplican a integración embebida)

Las pruebas referentes al panel administrativo no aplican al entorno embebido y se excluyen por completo.

🛡 Seguridad implementada para embeds

La integración Zajuna + Híbrida implementa:

CSP estricta:
default-src 'self'; frame-ancestors ...; script-src ...

CORS controlado:
solo dominios autorizados pueden consumir /chat o /api/chat.

Sandboxing natural del iframe, evitando acceso al contexto de la plataforma anfitriona.

Rate Limit configurable
Evita ataques o abuso desde el embed.

Protección de recursos estáticos
El widget solo accede a scripts autorizados.

🌐 Integración Embebida en la Plataforma Zajuna

Este chatbot puede integrarse dentro de Zajuna como iframe seguro, conservando todas las reglas de autenticación y sin exponer credenciales del usuario.

1️⃣ Requisitos en Zajuna

Debe permitir iframes del dominio del chatbot.

Zajuna debe exponer una función global:

window.getZajunaToken = () => "<JWT_DEL_USUARIO>";


El widget del chatbot nunca accede directamente al almacenamiento de Zajuna → solo usa esta función, si existe.

2️⃣ Código de integración en Zajuna
<script src="https://TU_DOMINIO/static/widget/chat-widget.js"
  data-chat-url="/chat-embed.html?embed=1"
  data-allowed-origins="https://app.zajuna.edu"
  data-login-url="https://app.zajuna.edu/login"
  data-badge="auto"></script>


Zajuna administra el token, el chatbot solo lo solicita cuando detecta un flujo privado:

iframe → auth:needed  
Zajuna → auth:token:"<JWT>"

3️⃣ Funcionalidades probadas en Zajuna

X-Request-ID propagado backend → Rasa → logs.

Scripts del launcher validados contra el origin real de Zajuna.

Flujo privado (consultar certificados) → requiere token.

Flujo público (FAQs, contenidos transversales) → no requiere token.

Badge dinámico sincronizado con la UI interna de Zajuna.

4️⃣ Resultado

La integración embebida funciona correctamente dentro de Zajuna, con seguridad garantizada por:

CSP estricta

Validación de origen

Mensajería controlada

Token nunca expuesto

Backend determinista según Authorization real