📘 README — Integración Embebida del Chatbot Tutor Virtual en la Plataforma ZAJUNA

Este documento describe cómo la Plataforma Zajuna puede incrustar (embed) el Chatbot Tutor Virtual de manera segura, aislada y confiable, manteniendo compatibilidad con los flujos académicos existentes y sin comprometer autenticación, tokens o datos de usuario.

El mecanismo implementado sigue estándares modernos:
✔ iframe + postMessage
✔ Validación estricta de orígenes
✔ Tokens controlados únicamente por Zajuna
✔ CSP endurecida
✔ Trazabilidad con X-Request-ID
✔ Protección contra framing no autorizado

1️⃣ Objetivo

Permitir que Zajuna incruste el Chatbot Tutor Virtual dentro de cualquier pantalla de su sistema, manteniendo:

Seguridad de sesión

Control del token por parte de Zajuna

Integridad del flujo conversacional

Aislamiento del iframe

Auditoría completa (backend → Rasa → logs)

2️⃣ Arquitectura de Integración
Zajuna (host)
   │
   │  (script) chat-widget.js
   ▼
Iframe: /chat-embed.html?embed=1
   │
   ├── postMessage → host (badge, auth, visibility)
   └── backend FastAPI ←→ Rasa (REST/webhook)


✔ El host (Zajuna) controla autenticación.
✔ El iframe nunca accede al localStorage de Zajuna.
✔ Comunicación validada por dominios autorizados.

3️⃣ Inserción del widget en Zajuna

Pegar este bloque dentro de la plantilla/layout de Zajuna:

<script src="https://TU_DOMINIO_CHATBOT/static/widget/chat-widget.js"
  data-chat-url="/chat-embed.html?embed=1"
  data-allowed-origins="https://app.zajuna.edu"
  data-login-url="https://app.zajuna.edu/login"
  data-badge="auto"></script>

Parámetros
Atributo	Descripción
data-chat-url	Ruta del iframe del chatbot
data-allowed-origins	Lista de orígenes permitidos (solo Zajuna)
data-login-url	URL del login real del SENA / Zajuna
data-badge	“auto” → activa el contador de mensajes
4️⃣ Autenticación: flujo seguro controlado por Zajuna

Zajuna debe exponer una función global:

window.getZajunaToken = () => localStorage.getItem("zajuna_token");

Flujo
1) El iframe detecta flujo privado (certificados, notas, etc.)
2) Solicita: postMessage({type:"auth:needed"})
3) Zajuna responde con: postMessage({type:"auth:token", token})
4) Backend valida JWT → metadata.auth.hasToken = true


⚠ El iframe nunca accede al localStorage de Zajuna.
⚠ Zajuna nunca envía más información que un JWT.

5️⃣ Seguridad (CSP, CORS y validación)
🔐 Medidas implementadas

✔ Validación estricta de origin y source
✔ targetOrigin forzado en cada postMessage
✔ CSP que protege iframe y scripts
✔ Anti-clickjacking: frame-ancestors
✔ Sanitización de mensajes JSON enviados al iframe
✔ Tokens no persistidos en el iframe
✔ Backend determina si el flujo es público/privado según Authorization real

🔏 Ejemplo de CSP recomendada para Nginx
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  frame-ancestors https://app.zajuna.edu;
  connect-src 'self' https://app.zajuna.edu https://TU_DOMINIO_CHATBOT;

6️⃣ Flujo privado vs. público
Tipo de flujo	Requiere token	Ejemplo	Comportamiento
Público	❌ No	FAQs, cursos, orientación	Backend fuerza hasToken=false
Privado	✔ Sí	/ver_certificados	Backend solicita login o activa flujo privado
7️⃣ Sistema de Badge / Notificaciones

El iframe envía:

postMessage({type:"chat:badge", count})


Zajuna puede mostrar un “puntico” o número en su header.

Cuando el usuario abre el chat, Zajuna responde:

postMessage({type:"chat:visibility", open:true})


🔁 Esto resetea el contador tanto en el host como dentro del iframe.

8️⃣ Pruebas realizadas dentro de Zajuna
✔ Flujo público probado con éxito

/explorar_temas

Carruseles (Excel / Soldadura / Web)

Cursos recomendados con tarjetas

Quick replies

✔ Flujo privado probado

/ver_certificados
→ SIN token → mensaje “Debe iniciar sesión”
→ CON token → listado de certificados + botones

✔ Interoperabilidad interna

X-Request-ID generado por backend y propagado a Rasa

Logs correlacionados en sistema.log

Validación origin/csource superada

Badge embebido funcionando

9️⃣ Health checks (ZAJUNA → Chatbot)

Desde backend:

GET /health
GET /chat/health
GET /chat/debug   (solo DEBUG=true)


Desde Nginx:

GET /api/chat/health
GET /rasa/status

🔟 Troubleshooting dentro de Zajuna
❌ El chatbot no se muestra

✔ Revisar CSP de Zajuna
✔ Revisar frame-ancestors

❌ El badge no sube o no baja

✔ Validar que Zajuna tenga listener:

window.addEventListener("message", ev => console.log(ev.data, ev.origin));

❌ “Debe iniciar sesión” incluso logueado

✔ Confirmar que getZajunaToken() retorna un JWT real
✔ Verificar encabezado “Authorization: Bearer …” en DevTools

❌ Error CORS

✔ Confirmar que el dominio Zajuna está en ALLOWED_ORIGINS del backend
✔ Confirmar VITE_ALLOWED_HOST_ORIGINS del widget

1️⃣1️⃣ Archivos relevantes
Archivo	Ubicación
Widget embebido	/static/widget/chat-widget.js
UI del iframe	/chat-embed.html
Lógica UI	frontend/src/chat/ChatUI.jsx
Badge	frontend/src/components/Badge.jsx
Listener principal	frontend/src/components/Header.jsx
Pruebas Zajuna	TESTING.md
CSP Nginx	ops/nginx/conf.d/prod/default.conf
1️⃣2️⃣ Conclusión

La plataforma Zajuna puede integrar el Chatbot Tutor Virtual de forma segura, validada y funcional, sin exposición de credenciales, con auditoría completa y flujos privados/públicos totalmente operativos.

La integración ha sido probada, validada y documentada, siendo apta para entornos institucionales como el SENA.