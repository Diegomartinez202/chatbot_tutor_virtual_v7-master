📄 docs/README_embed.md
Chatbot Tutor Virtual — Guía de Embed para Zajuna

Objetivo. Incrustar el Chatbot Tutor Virtual del SENA en la plataforma Zajuna de forma segura, desacoplada y sin cambios en la arquitectura existente.

1) Opciones de integración
A. Launcher (botón flotante + panel con iframe) — recomendado

Inserta este script en la plantilla principal (footer):

<!-- Chatbot Tutor Virtual SENA: Launcher (botón flotante) -->
<script
  src="https://chatbot-tutor.sena.edu.co/chat-widget.js"
  data-chat-url="/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px&title=Chatbot%20Tutor&avatar=%2Fbot-avatar.png"
  data-avatar="/bot-avatar.png"
  data-title="Abrir chat"
  data-position="bottom-right"
  data-panel-width="380px"
  data-panel-height="560px"
  data-allowed-origins="https://zajuna.edu.co,https://app.zajuna.edu.co"
  data-login-url="https://zajuna.edu.co/login"
  data-badge="auto"
  defer>
</script>


Qué hace:

Muestra un botón flotante (“Abrir chat”).

Al hacer clic, abre un panel con un iframe que carga chat-embed.html, el cual a su vez muestra el chat real mediante src=/chat?embed=1.

B. Embed directo (solo iframe)

Inserta el chat directamente donde quieras que aparezca:

<!-- Chatbot Tutor Virtual SENA: Embed directo -->
<iframe
  src="https://chatbot-tutor.sena.edu.co/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px"
  title="Chatbot Tutor Virtual"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:380px;height:560px;border:0;border-radius:16px;overflow:hidden">
</iframe>


Nota: El parámetro src=%2Fchat%3Fembed%3D1 (url-encoded) es obligatorio para renderizar el chat real en modo embed.

2) Parámetros útiles

Tamaño del panel (launcher)
data-panel-width="380px" y data-panel-height="560px"

Posición del botón
data-position="bottom-right" o bottom-left

Orígenes permitidos (postMessage)
data-allowed-origins="https://zajuna.edu.co,https://app.zajuna.edu.co"

SSO / Login (si no hay token)
data-login-url="https://zajuna.edu.co/login"

Ancho/alto del embed directo (iframe)
?w=380px&h=560px (también soporta vw / vh)

3) Seguridad

HTTPS obligatorio (tanto Zajuna como el dominio del chatbot).

CSP / Iframe: habilitar frame-ancestors / EMBED_ALLOWED_ORIGINS para los dominios de Zajuna.

CORS: el backend del chatbot debe permitir los orígenes de Zajuna.

postMessage seguro: el launcher valida los orígenes definidos en data-allowed-origins.

Sandbox del iframe (embed directo):
sandbox="allow-scripts allow-forms allow-same-origin allow-popups"

4) Handshake de autenticación (opcional)

El iframe del chat solicita autenticación con
postMessage({ type: "auth:needed" }).

El launcher intenta inyectar un token (por ejemplo desde localStorage.zajuna_token o window.getZajunaToken()) y responde con
postMessage({ type: "auth:token", token }).

Si no hay token y se configuró data-login-url, redirige a esa URL con ?redirect=<url-actual>.

Esto permite que el chatbot actúe en nombre del usuario autenticado en Zajuna.

5) Telemetría (opcional)

Si desean recolectar eventos (apertura/cierre del widget, contador de no leídos), pueden incluir este script después del launcher:

<script src="https://chatbot-tutor.sena.edu.co/chat-telemetry.sample.js" defer></script>


Ese script envía eventos con navigator.sendBeacon("/telemetry", …) (pueden modificar la URL y formato).

6) Troubleshooting

No se ve el chat / 403 / 401: revisar CORS y CSP (iframe) en el servidor del chatbot.

No aparece el botón: revisar que el <script … defer> del launcher esté cargando sin bloqueos (errores en consola).

SSO no funciona: verificar que data-login-url apunte a la ruta correcta y que, tras login, el token esté disponible para el host.

7) Branding y assets

Avatar: https://chatbot-tutor.sena.edu.co/bot-avatar.png

Favicon / manifest (si se desea enlazar):
https://chatbot-tutor.sena.edu.co/favicon.ico
https://chatbot-tutor.sena.edu.co/site.webmanifest

Pueden reemplazar el avatar por imágenes propias del SENA/Zajuna si lo prefieren.

8) Contacto técnico

Equipo Chatbot Tutor Virtual — SENA

Correo/Canal: (completar por el equipo del chatbot)

Requisitos para Go-Live: dominios de Zajuna en CSP/iframe, CORS y data-allowed-origins.

9) Resumen ejecutivo

El Chatbot Tutor Virtual se integra en Zajuna con un solo snippet (script o iframe), de forma segura, modular y no intrusiva. El widget se actualiza sin intervenir el core de Zajuna, permite operación 24/7 y escala con las necesidades del SENA.

Anexos (opcional)

Web Component (si prefieren un custom element encapsulado):

<script src="https://chatbot-tutor.sena.edu.co/zajuna-widget.webc.js" defer></script>
<chatbot-tutor-sena
  origin="https://chatbot-tutor.sena.edu.co"
  path-embed="/chat-embed.html"
  chat-src="/chat?embed=1"
  width="380px"
  height="560px"
  title="Chatbot Tutor Virtual"
  avatar="/bot-avatar.png">
</chatbot-tutor-sena>


Versión del documento: 1.0 — Fecha: 08/18/2025