# README – Embed Híbrido del Chatbot Tutor Virtual

Este README explica cómo **embeber** el chat en un portal (host) y habilitar **autenticación diferida**: el chat funciona como invitado y **pide token** solo cuando una acción sensible lo requiere (estado, certificados, tutor, etc.).

## 1) Archivos clave

- `admin_panel_react/public/hybrid-host.html`  
  Host de prueba que **contiene el iframe** del chat (`/chat?embed=1&guest=1`), con:
  - Botón “Iniciar sesión” (Zajuna).
  - Botón “Abrir chat autenticado” (chat web normal).
  - `postMessage('auth:request')` ← `auth:token` (flujo híbrido).

- `admin_panel_react/src/components/chat/ChatUI.jsx`  
  Implementa **sendToRasa con auth diferida**:
  - Si el intent está en `NEED_AUTH` y **no hay token**, el cliente:
    - Envía `window.parent.postMessage({type:'auth:request'})`
    - Muestra CTA de login (VITE_LOGIN_URL)
    - **No llama a Rasa** hasta que llegue el token.

- `ops/nginx/conf.d/prod/default.conf`  
  CSP para permitir que el chat sea **embeber** por el host (frame-ancestors) y que el host cargue el iframe del chat (frame-src).

## 2) Rutas de prueba

- Chat embebido: `http://localhost:8080/hybrid-host.html`  
- Chat web normal: `http://localhost:8080/chat` (sin `embed=1`)

## 3) Variables de entorno (frontend)

VITE_LOGIN_URL=https://zajuna.sena.edu.co/
VITE_ALLOWED_HOST_ORIGINS=https://zajuna.sena.edu.co,http://localhost:8080
VITE_CHAT_TRANSPORT=rest

pgsql
Copiar código

## 4) Nginx (CSP)

**Servidor del chat** (`ops/nginx/conf.d/prod/default.conf`):
```nginx
add_header Content-Security-Policy "default-src 'self';
  img-src 'self' data: https:;
  media-src 'self' https:;
  connect-src 'self' https:;
  frame-ancestors 'self' https://zajuna.sena.edu.co http://localhost:8080 http://localhost:5173;
  upgrade-insecure-requests" always;
add_header Permissions-Policy "microphone=(), camera=()" always;
Servidor host (si es otro vhost):

nginx
Copiar código
set $chat_host "https://zajuna.sena.edu.co http://localhost:5173 http://localhost:8080";
add_header Content-Security-Policy "default-src 'self';
  img-src 'self' data: https:;
  media-src 'self' https:;
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  connect-src 'self' https:;
  frame-src 'self' $chat_host;
  frame-ancestors 'self';
  upgrade-insecure-requests" always;
add_header Permissions-Policy "microphone=(), camera=()" always;
5) Flujo de autenticación
El usuario envía un intent sensible (p. ej. /estado_estudiante).

Si no hay token: ChatUI envía auth:request → el host responde con auth:token.

Con token, ChatUI llama una sola vez a sendToRasaREST(senderId, text, token) y continúa el flujo en el mismo iframe.

Opcional: el host también ofrece “Abrir chat autenticado” en otra pestaña.

6) Pruebas rápidas
Abre hybrid-host.html → haz clic en “Simular guardar token” y luego “Abrir chat”.

Envía un intent sensible: el iframe no debería pedir token (ya fue enviado).

Borra token y repite: ahora el iframe pedirá login (CTA + auth:request).

7) Producción
Mantén el /chat sin embed=1 para el chat web normal.

Usa /chat?embed=1&guest=1 en el iframe del portal host.

Asegura CSP y HTTPS en ambos (host y chat).

yaml
Copiar código

---

# 3) Informe-tecnico-flujo-hibrido.md (listo para Word)

> Pégalo tal cual en Word con portada del SENA. Está redactado para sustentación.

```md
# Informe Técnico – Flujo Híbrido (Embed + Web) del Chatbot Tutor Virtual

**Proyecto:** Chatbot Tutor Virtual – Integración híbrida con Zajuna  
**Autor:** Daniel Hernán Martínez Cano  
**Fecha:** [colocar fecha de entrega]  
**Versión:** 1.0

---

## 1. Resumen Ejecutivo
Se implementó un **flujo híbrido** de conversación para el Chatbot Tutor Virtual, combinando:
- **Modo Invitado** (FAQ públicas) sin autenticación.
- **Modo Autenticado** para acciones sensibles (estado académico, certificados, tutor asignado, etc.), con **autenticación diferida**:
  - En **embed** (iframe): el chat solicita token al **host** mediante `postMessage('auth:request')` y muestra una **CTA de login**. El host responde con `postMessage('auth:token', token)`. Con token presente, el flujo continúa **en el mismo iframe**.
  - En **web** (no embed): muestra CTA a `/login` y/o URL del portal Zajuna.

La solución **no rompe** el flujo actual, habilita transición a **SSO/OIDC** y mantiene el **panel administrativo** con roles.

---

## 2. Objetivo
Garantizar un chat **seguro, escalable y desacoplado**, que funcione sin login para consultas generales, pero **exija autenticación** solo cuando el usuario lo requiera, sin forzar redirecciones ni recargar el iframe.

---

## 3. Alcance
- **Frontend (React)**  
  - `ChatUI.jsx`: reemplazo de `sendToRasa` por una versión con **auth diferida**.
  - `ChatPage.jsx`: admite `embed=1` para modo embebido; `embed=0`/sin flag para chat web.
  - `hybrid-host.html`: host de pruebas con iframe, **CTA** y `postMessage` de token.
- **Backend (FastAPI)**  
  - Sin cambios funcionales: el endpoint de chat REST ya acepta `metadata.auth`/token.
- **Rasa**  
  - Mantener intents sensibles en un set (`NEED_AUTH`) y/o `utter_need_auth`.
- **Nginx (CSP)**  
  - `frame-ancestors` (chat) y `frame-src` (host) configurados.

---

## 4. Arquitectura Lógica

**Componentes:**
- **Host** (portal Zajuna u host de demo `hybrid-host.html`): contiene la UI y el iframe. Gestiona **token** del usuario y responde a `auth:request`.
- **Chat Web** (`/chat`): render directo de `ChatUI` cuando no es embebido.
- **Chat Embebido** (`/chat?embed=1&guest=1`): ejecuta **auth diferida** para intents sensibles.
- **Backend** (FastAPI): proxy/servicios del chat.
- **Rasa**: NLU/NLG/acciones.  

**Diagrama de secuencia (texto):**
1. Usuario (embed) → Bot: `/estado_estudiante`  
2. `ChatUI` detecta intent sensible + **no token** → `postMessage('auth:request')` + CTA login.  
3. Host → `postMessage('auth:token', token)`.  
4. `ChatUI` reintenta → `sendToRasaREST(senderId, text, token)`.  
5. Rasa responde y el flujo continúa dentro del **mismo iframe**.

---

## 5. Seguridad
- **CSP:**  
  - Chat server con `frame-ancestors` para permitir host(s) legítimos (Zajuna/localhost).  
  - Host con `frame-src` para permitir iframes desde el dominio del chat.
- **Permisos-Policy:** `microphone=(), camera=()` por defecto.
- **Tokens:** solo **en memoria/localStorage del host**. El intercambio con el iframe es por `postMessage` filtrando `origin`.
- **CORS/WebSockets:** gobernados en Nginx y/o FastAPI según perfiles dev/prod.

---

## 6. Configuración y Despliegue

**Variables frontend:**
VITE_LOGIN_URL=https://zajuna.sena.edu.co/
VITE_ALLOWED_HOST_ORIGINS=https://zajuna.sena.edu.co,http://localhost:8080
VITE_CHAT_TRANSPORT=rest

pgsql
Copiar código

**Nginx del chat:**
```nginx
add_header Content-Security-Policy "default-src 'self';
  img-src 'self' data: https:;
  media-src 'self' https:;
  connect-src 'self' https:;
  frame-ancestors 'self' https://zajuna.sena.edu.co http://localhost:8080 http://localhost:5173;
  upgrade-insecure-requests" always;
add_header Permissions-Policy "microphone=(), camera=()" always;
Nginx del host:

nginx
Copiar código
set $chat_host "https://zajuna.sena.edu.co http://localhost:5173 http://localhost:8080";
add_header Content-Security-Policy "default-src 'self';
  img-src 'self' data: https:;
  media-src 'self' https:;
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  connect-src 'self' https:;
  frame-src 'self' $chat_host;
  frame-ancestors 'self';
  upgrade-insecure-requests" always;
add_header Permissions-Policy "microphone=(), camera=()" always;
7. Pruebas (Plan y Evidencias)
Pruebas funcionales (embed):

P1: Sin token → enviar /faq (debe responder normal).

P2: Sin token → enviar /estado_estudiante (debe mostrar CTA + emitir auth:request).

P3: Host guarda token (host_token) → se envía auth:token → repetir /estado_estudiante (fluye normal).

Pruebas funcionales (web):

P4: /chat sin login → CTA a /login/Zajuna si el intent es sensible.

P5: /chat con login → intents sensibles funcionan.

Pruebas de seguridad:

P6: iFrame en host no permitido → el chat no carga (CSP).

P7: PostMessage desde origen no permitido → el host lo descarta.

8. Resultados
Chat híbrido operativo con auth diferida.

Sin ruptura del flujo embebido; transición a login cuando corresponde.

Preparado para SSO/OIDC con Zajuna (en el futuro).

9. Conclusiones y Trabajo Futuro
El enfoque desacoplado (postMessage + CSP) es seguro y escalable.

Próximo paso: consolidar OIDC/SSO con intercambio formal de token y roles para el panel admin.

Añadir telemetría/analytics del evento auth:request/auth:token y métricas de intents sensibles.

10. Anexos
admin_panel_react/public/hybrid-host.html (host de demo).

Extractos de ChatUI.jsx (sendToRasa con auth diferida).

Snippets de Nginx (CSP).