# Chatbot Tutor Virtual — Guía de *Embed* para Zajuna

> Objetivo: Incrustar el **Chatbot Tutor Virtual del SENA** en **Zajuna** de forma **segura, desacoplada** y **sin cambios** en la arquitectura existente.

---

## 1) Opciones de integración

### A. Launcher (botón flotante + panel con iframe) — recomendado
Inserta este script en la plantilla (footer):

```html
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
Qué hace: muestra un botón flotante; al clic abre un panel con un iframe que carga chat-embed.html → src=/chat?embed=1.

B. Embed directo (solo iframe)
Coloca el chat directamente donde lo necesiten:

html
Copiar
Editar
<!-- Chatbot Tutor Virtual SENA: Embed directo -->
<iframe
  src="https://chatbot-tutor.sena.edu.co/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px"
  title="Chatbot Tutor Virtual"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:380px;height:560px;border:0;border-radius:16px;overflow:hidden">
</iframe>
src=%2Fchat%3Fembed%3D1 (URL-encoded) es obligatorio para renderizar el chat real en modo embed.

2) Parámetros útiles
Tamaño panel (launcher):
data-panel-width="380px", data-panel-height="560px"

Posición botón:
data-position="bottom-right" o bottom-left

Orígenes permitidos (postMessage):
data-allowed-origins="https://zajuna.edu.co,https://app.zajuna.edu.co"

SSO / Login (opcional):
data-login-url="https://zajuna.edu.co/login"

Iframe directo (ancho/alto):
?w=380px&h=560px (soporta vw/vh)

3) Seguridad
HTTPS en Zajuna y en el dominio del chatbot.

CSP / iframe: habilitar frame-ancestors/EMBED_ALLOWED_ORIGINS para dominios de Zajuna.

CORS: backend del chatbot debe permitir orígenes de Zajuna.

postMessage seguro: el launcher valida los orígenes de data-allowed-origins.

Sandbox del iframe (embed directo):
sandbox="allow-scripts allow-forms allow-same-origin allow-popups"

4) Handshake de autenticación (opcional)
El iframe pide auth con postMessage({ type: "auth:needed" }).

El launcher responde con postMessage({ type: "auth:token", token }) leyendo el token de localStorage.zajuna_token o window.getZajunaToken().

Si no hay token y existe data-login-url, se redirige a login con ?redirect=<url-actual>.

5) Telemetría (opcional)
Se puede incluir un script que envíe eventos (apertura, mensajes, badge).
Si lo desean, el equipo del chatbot proveerá una URL y formato.

6) Troubleshooting
No se ve el chat / 401-403: revisar CORS y CSP (iframe).

No aparece el botón: verificar carga del <script … defer> y consola del navegador.

SSO falla: validar data-login-url y disponibilidad del token tras el login.

7) Branding y assets
Avatar: https://chatbot-tutor.sena.edu.co/bot-avatar.png

Favicon/manifest opcionales:

https://chatbot-tutor.sena.edu.co/favicon.ico

https://chatbot-tutor.sena.edu.co/site.webmanifest

8) Contacto técnico
Equipo Chatbot Tutor Virtual — SENA

Canal de soporte: (completar)

9) Resumen
El chatbot se integra con un único snippet (script o iframe), de manera modular, segura y no intrusiva.