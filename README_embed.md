

md = r"""# Embed Guide — Chatbot Tutor Virtual (Completo)

Esta guía explica **cómo incrustar** el Chatbot Tutor Virtual en sitios externos (p. ej. **Zajuna**) usando:
- el **launcher público** (`public/chat-widget.js`, botón flotante + panel con iframe, `postMessage` seguro), y
- la **página canónica de embed** (`public/chat-embed.html`) que aloja el iframe del chat real (`/chat?embed=1`).

Incluye **snippets con entidades HTML** (seguros para editores que confunden HTML con JSX/TSX) y **snippets planos** listos para producción.
También encontrarás ejemplos de **CSP/CORS/NGINX**, **telemetría**, **zajuna widget.js** (loader), **Web Component**, y un **plan de transición a SSO/OIDC**.

> **Compatibilidad**: el **admin original** sigue siendo la base del embebido/acoplamiento; el **admin nuevo** (`/api/admin2/*`) se usa para la sustentación y operación mejorada. Conviven **sin romper** el servicio actual.

---

## 1) Arquitectura & archivos (frontend)

- `public/chat-widget.js` → **launcher** (botón flotante, panel con **iframe**, `postMessage` seguro, badge opcional).
- `public/chat-embed.html` → **contenedor canónico** que inyecta el iframe real del chat (`src=/chat?embed=1`).
- Activos: `public/bot-avatar.png`, `public/bot-loading.png`, `public/favicon.ico`, `public/site.webmanifest`.

> `chat-embed.html` requiere `?src=/chat?embed=1` (URL-encoded) para renderizar el chat real en modo embed.

---

## 2) Variables de entorno

**Frontend**
```bash
# Transporte
VITE_CHAT_TRANSPORT=rest         # o 'ws'
VITE_CHAT_REST_URL=/api/chat     # si 'rest' (proxy)
VITE_RASA_WS_URL=wss://TU-RASA/ws  # si 'ws'

# Seguridad postMessage (orígenes autorizados que pueden alojar el launcher/iframe)
VITE_ALLOWED_HOST_ORIGINS=https://app.zajuna.edu,http://localhost:5173

# Avatares
VITE_BOT_AVATAR=/bot-avatar.png
VITE_USER_AVATAR=/user-avatar.png  # opcional
Backend
Mostrar siempre los detalles
# CSP/iframe y control de embed
EMBED_ENABLED=true
FRAME_ANCESTORS=https://zajuna.sena.edu.co https://*.zajuna.sena.edu.co
EMBED_ALLOWED_ORIGINS=https://zajuna.sena.edu.co

# CORS
ALLOWED_ORIGINS=https://zajuna.sena.edu.co

# URLs públicas (si tu backend sirve el frontend)
FRONTEND_SITE_URL=https://chatbot.sena.edu.co
________________________________________
3) Snippet del Launcher (botón flotante)
3.1 Versión con entidades HTML (segura para editores)
Mostrar siempre los detalles
&lt;script src="/chat-widget.js"
         data-chat-url="/chat-embed.html?src=%2Fchat%3Fembed%3D1&amp;w=380px&amp;h=560px&amp;title=Chatbot%20Tutor&amp;avatar=%2Fbot-avatar.png"
         data-avatar="/bot-avatar.png"
         data-title="Abrir chat"
         data-position="bottom-right"
         data-panel-width="380px"
         data-panel-height="560px"
         data-allowed-origins="https://tu-sitio.com,https://app.zajuna.edu"
         data-login-url="https://zajuna.edu/login"
         data-badge="auto"
         defer&gt;&lt;/script&gt;
3.2 Versión plana (producción)
Mostrar siempre los detalles
<script src="/chat-widget.js"
        data-chat-url="/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px&title=Chatbot%20Tutor&avatar=%2Fbot-avatar.png"
        data-avatar="/bot-avatar.png"
        data-title="Abrir chat"
        data-position="bottom-right"
        data-panel-width="380px"
        data-panel-height="560px"
        data-allowed-origins="https://tu-sitio.com,https://app.zajuna.edu"
        data-login-url="https://zajuna.edu/login"
        data-badge="auto"
        defer></script>
Notas
•	data-chat-url debe incluir src=/chat?embed=1 (URL-encoded) para cargar el chat real dentro de chat-embed.html.
•	data-allowed-origins contiene el origin del iframe.
•	data-login-url habilita SSO/redirect si falta token.
•	data-badge="auto" muestra no leídos (si tu ChatUI emite chat:badge).
________________________________________
4) Embed directo (iframe)
4.1 Con entidades HTML
Mostrar siempre los detalles
&lt;iframe
  src="/chat-embed.html?src=%2Fchat%3Fembed%3D1&amp;w=380px&amp;h=560px"
  title="Chatbot"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:380px;height:560px;border:0;border-radius:16px;overflow:hidden"&gt;
&lt;/iframe&gt;
4.2 Plano
Mostrar siempre los detalles
<iframe
  src="/chat-embed.html?src=%2Fchat%3Fembed%3D1&w=380px&h=560px"
  title="Chatbot"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:380px;height:560px;border:0;border-radius:16px;overflow:hidden">
</iframe>
________________________________________
5) Handshake de autenticación (postMessage)
1.	El iframe emite: postMessage({ type: "auth:needed" }).
2.	El launcher intenta obtener token: window.getZajunaToken(), window.ZAJUNA_TOKEN, localStorage.zajuna_token.
3.	Si existe token → responde postMessage({ type: "auth:token", token }).
4.	Si no hay token y existe data-login-url, redirige a ?redirect=<url-actual>.
Requisitos
•	VITE_ALLOWED_HOST_ORIGINS y CSP frame-ancestors deben incluir el dominio anfitrión.
•	Backend acepta Authorization: Bearer <token> en /api/chat (o el proxy que uses).
________________________________________
6) Transporte (REST / WebSocket)
REST (default)
Mostrar siempre los detalles
VITE_CHAT_TRANSPORT=rest
VITE_CHAT_REST_URL=/api/chat
WS
Mostrar siempre los detalles
VITE_CHAT_TRANSPORT=ws
VITE_RASA_WS_URL=wss://tu-servidor-de-rasa/ws
El ChatUI/launcher seleccionan transporte por VITE_CHAT_TRANSPORT.
________________________________________
7) chat-embed.html (sugerencia de implementación)
Minimalista, ajusta estilos/CSP según tu hosting.
Mostrar siempre los detalles
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Chat Embed</title>
    <style>
      html,body { margin:0; padding:0; height:100%; }
      .wrap { display:flex; align-items:center; justify-content:center; height:100%; background:#fff; }
      iframe.chat { width: var(--w, 380px); height: var(--h, 560px); border:0; border-radius: 16px; }
    </style>
    <script>
      (function(){
        const p = new URLSearchParams(location.search);
        const w = p.get("w") || "380px";
        const h = p.get("h") || "560px";
        const src = p.get("src") || "/chat?embed=1";
        const api = p.get("api");
        const avatar = p.get("avatar");
        const userId = p.get("user_id");
        const inner = new URL(src, location.origin);
        if (api)   inner.searchParams.set("api", api);
        if (avatar)inner.searchParams.set("avatar", avatar);
        if (userId)inner.searchParams.set("user_id", userId);
        document.documentElement.style.setProperty("--w", w);
        document.documentElement.style.setProperty("--h", h);
        window.__CHAT_SRC__ = inner.toString();
        window.addEventListener("message", (ev) => {
          // Propaga eventos si necesitas (badge, visibilidad, etc.).
          // Ej: if (ev.data?.type === "chat:badge") parent.postMessage(ev.data, "*");
        });
      })();
    </script>
  </head>
  <body>
    <div class="wrap">
      <iframe class="chat" title="Chatbot Tutor Virtual" src="" allow="clipboard-write" sandbox="allow-scripts allow-forms allow-same-origin allow-popups"></iframe>
    </div>
    <script>
      (function(){
        const f = document.querySelector("iframe.chat");
        f.src = window.__CHAT_SRC__ || "/chat?embed=1";
      })();
    </script>
  </body>
</html>
________________________________________
8) chat-widget.js (launcher) — ejemplo completo
Este esqueleto monta un botón flotante, abre/cierra un panel, maneja postMessage, soporte de badge, y handshake de auth con origen verificado.
Mostrar siempre los detalles
(() => {
  const cfg = document.currentScript?.dataset || {};
  const chatUrl = cfg.chatUrl || "/chat-embed.html?src=%2Fchat%3Fembed%3D1";
  const avatar = cfg.avatar || "/bot-avatar.png";
  const title  = cfg.title || "Abrir chat";
  const pos    = (cfg.position || "bottom-right").toLowerCase();
  const panelW = cfg.panelWidth || "380px";
  const panelH = cfg.panelHeight || "560px";
  const zIndex = Number.isFinite(Number(cfg.zIndex)) ? Number(cfg.zIndex) : 2147483600;
  const loginUrl = cfg.loginUrl || "";
  const badgeMode = cfg.badge || ""; // "", "auto" o número fijo
  const allowed = (cfg.allowedOrigins || "")
    .split(",")
    .map(s => s.trim())
    .filter(Boolean);

  const style = document.createElement("style");
  style.textContent = `
    .ctv-launcher{position:fixed;${pos.includes("left")?"left":"right"}:20px;bottom:20px;width:56px;height:56px;border-radius:999px;border:0;background:#2563eb;color:#fff;
      box-shadow:0 10px 20px rgba(0,0,0,.25);font-weight:600;cursor:pointer;z-index:${zIndex+1};display:flex;align-items:center;justify-content:center}
    .ctv-badge{position:absolute;top:-6px;right:-6px;background:#ef4444;color:#fff;border-radius:999px;min-width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:11px;padding:0 4px}
    .ctv-panel{position:fixed;${pos.includes("left")?"left":"right"}:20px;bottom:90px;width:${panelW};height:${panelH};border:0;border-radius:16px;display:none;z-index:${zIndex};box-shadow:0 20px 40px rgba(0,0,0,.25);background:#fff;overflow:hidden}
    .ctv-overlay{position:fixed;inset:0;background:rgba(0,0,0,.3);display:none;z-index:${zIndex-1}}
    @media (max-width:480px){.ctv-panel{width:94vw;height:70vh;${pos.includes("left")?"left":"right"}:3vw}}
  `;
  document.head.appendChild(style);

  const overlay = document.createElement("div");
  overlay.className = "ctv-overlay";
  document.body.appendChild(overlay);

  const btn = document.createElement("button");
  btn.className = "ctv-launcher"; btn.type = "button"; btn.setAttribute("aria-label", title);
  btn.innerHTML = avatar ? `<img src="${avatar}" alt="" style="width:28px;height:28px;border-radius:50%"/>` : "Chat";
  const badge = document.createElement("span"); badge.className="ctv-badge"; badge.style.display="none"; badge.textContent="0";
  btn.style.position="fixed"; btn.appendChild(badge);

  const panel = document.createElement("iframe");
  panel.className = "ctv-panel";
  panel.title = cfg.iframeTitle || "Chat";
  panel.allow = cfg.allow || "clipboard-write";
  panel.sandbox = cfg.sandbox || "allow-scripts allow-forms allow-same-origin allow-popups";
  panel.src = chatUrl;

  function open(){ overlay.style.display="block"; panel.style.display="block"; window.dispatchEvent(new CustomEvent("ctv:widget-opened")); btn.setAttribute("aria-expanded","true"); }
  function close(){ overlay.style.display="none"; panel.style.display="none"; window.dispatchEvent(new CustomEvent("ctv:widget-closed")); btn.setAttribute("aria-expanded","false"); }
  btn.addEventListener("click", () => { (panel.style.display==="block") ? close() : open(); });
  overlay.addEventListener("click", close);
  window.addEventListener("keydown", (e)=>{ if(e.key==="Escape") close(); });

  // postMessage seguro (badge, auth)
  function isAllowed(origin){
    if (allowed.length === 0) return true; // si no se configuró, permite same-origin del iframe
    try { return allowed.includes(new URL(origin).origin); } catch { return false; }
  }
  window.addEventListener("message", (ev) => {
    const data = ev.data || {};
    if (!isAllowed(ev.origin)) return;

    // Badge (no leídos)
    if (data.type === "chat:badge") {
      if (badgeMode === "auto") {
        const n = Number(data.count || 0);
        badge.style.display = n > 0 ? "flex" : "none";
        badge.textContent = String(n);
        window.dispatchEvent(new CustomEvent("ctv:badge", { detail: { count: n }}));
      }
    }

    // Auth handshake
    if (data.type === "auth:needed") {
      let token = "";
      try { token = (window.getZajunaToken && window.getZajunaToken()) || window.ZAJUNA_TOKEN || localStorage.getItem("zajuna_token") || ""; } catch {}
      if (token) {
        panel.contentWindow?.postMessage({ type:"auth:token", token }, "*");
      } else if (loginUrl) {
        const redirect = encodeURIComponent(window.location.href);
        window.location.href = `${loginUrl}?redirect=${redirect}`;
      }
    }

    // Visibilidad (opcional)
    if (data.type === "chat:visibility") {
      if (data.open) open(); else close();
    }
  });

  // Modo autoinit (por defecto true)
  const autoinit = String(cfg.autoinit ?? "true").toLowerCase() !== "false";
  if (autoinit) {
    document.body.appendChild(btn);
    document.body.appendChild(panel);
  }
})();
________________________________________
9) NGINX / Seguridad backend (CSP/CORS)
CSP (ejemplo)
Mostrar siempre los detalles
add_header Content-Security-Policy "frame-ancestors https://zajuna.sena.edu.co https://*.zajuna.sena.edu.co" always;
add_header X-Content-Type-Options "nosniff" always;
CORS (solo para APIs admin/REST)
Mostrar siempre los detalles
location /api/ {
  if ($http_origin = "https://zajuna.sena.edu.co") {
    add_header "Access-Control-Allow-Origin" "$http_origin";
    add_header "Vary" "Origin";
  }
  proxy_pass http://fastapi_upstream;
}
.env backend (JWT/cookies)
Mostrar siempre los detalles
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
COOKIE_SECURE=true
SAMESITE=Lax
________________________________________
10) Parámetros chat-embed.html (query)
Parámetro	Tipo	Default	Ejemplo	Reenvía al iframe	Descripción
src	string	/chat?embed=1	/chat%3Fembed%3D1	✅	Origen del chat interno (obligatorio).
w	string	380px	92vw	❌	Ancho visual.
h	string	560px	70vh	❌	Alto visual.
api	string	—	https://backend.tuapp.com/api	✅	Base de API/Proxy (si aplica).
user_id	string	—	alumno-123	✅	Identificador (tracking/sesión).
avatar	string	—	/bot-avatar.png	✅	Avatar del bot (si lo soporta el iframe).
Ejemplos con entidades HTML
Mostrar siempre los detalles
&lt;iframe
  src="/chat-embed.html?src=%2Fchat%3Fembed%3D1&amp;w=380px&amp;h=560px"
  title="Chatbot"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:380px;height:560px;border:0;border-radius:16px;overflow:hidden"&gt;
&lt;/iframe&gt;
Mostrar siempre los detalles
&lt;iframe
  src="/chat-embed.html?src=%2Fchat%3Fembed%3D1&amp;api=https%3A%2F%2Fbackend.tuapp.com%2Fapi&amp;user_id=alumno-123"
  title="Chatbot"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:380px;height:560px;border:0;border-radius:16px;overflow:hidden"&gt;
&lt;/iframe&gt;
Mostrar siempre los detalles
&lt;iframe
  src="/chat-embed.html?src=%2Fchat%3Fembed%3D1&amp;w=92vw&amp;h=70vh"
  title="Chatbot"
  allow="clipboard-write"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
  style="width:92vw;height:70vh;border:0;border-radius:16px;overflow:hidden"&gt;
&lt;/iframe&gt;
________________________________________
11) Telemetría (opcional)
Eventos DOM emitidos por el launcher
Mostrar siempre los detalles
// dentro de open()
window.dispatchEvent(new CustomEvent("ctv:widget-opened"));
// dentro de close()
window.dispatchEvent(new CustomEvent("ctv:widget-closed"));
// cuando recibes chat:badge
window.dispatchEvent(new CustomEvent("ctv:badge", { detail: { count: data.count } }));
Listener de ejemplo (public/chat-telemetry.sample.js)
Mostrar siempre los detalles
window.addEventListener("ctv:widget-opened", () => {
  try { navigator.sendBeacon("/telemetry", JSON.stringify({ e: "widget_opened", t: Date.now() })); } catch {}
});
window.addEventListener("ctv:widget-closed", () => {
  try { navigator.sendBeacon("/telemetry", JSON.stringify({ e: "widget_closed", t: Date.now() })); } catch {}
});
window.addEventListener("ctv:badge", (ev) => {
  try { navigator.sendBeacon("/telemetry", JSON.stringify({ e: "badge", count: ev.detail?.count ?? 0, t: Date.now() })); } catch {}
});
Uso
Mostrar siempre los detalles
<script src="/chat-widget.js" data-chat-url="/chat-embed.html?src=%2Fchat%3Fembed%3D1" defer></script>
<script src="/chat-telemetry.sample.js" defer></script>
________________________________________
12) (Opcional) Loader public/zajuna-widget.js
Mostrar siempre los detalles
(() => {
  const s = document.currentScript?.dataset || {};
  const origin = (s.origin || window.location.origin).replace(/\/$/, "");
  const pathEmbed = s.pathEmbed || "/chat-embed.html";
  const chatSrc = s.chatSrc || "/chat?embed=1";
  const width = s.width || "380px";
  const height = s.height || "560px";
  const position = s.position === "left" ? "left" : "right";
  const title = s.title || "Chatbot Tutor Virtual";
  const allow = s.allow || "clipboard-write";
  const sandbox = s.sandbox || "allow-scripts allow-forms allow-same-origin allow-popups";
  const z = Number.isFinite(Number(s.zIndex)) ? Number(s.zIndex) : 9999;

  const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(s.avatar || "/bot-avatar.png")}`;

  const style = document.createElement("style");
  style.textContent = `
    .zj-launcher { position:fixed; ${position}:20px; bottom:20px; width:56px; height:56px;
      border-radius:999px; border:0; cursor:pointer; background:#2563eb; color:#fff;
      box-shadow:0 10px 20px rgba(0,0,0,.25); font-weight:600; z-index:${z+1}; }
    .zj-frame { position:fixed; ${position}:20px; bottom:90px; width:${width}; height:${height};
      border:0; border-radius:16px; box-shadow:0 20px 40px rgba(0,0,0,.25);
      display:none; z-index:${z}; }
    .zj-frame.open { display:block; }
    @media (max-width:480px){ .zj-frame { width:94vw; height:70vh; ${position}:3vw; } }
  `;
  document.head.appendChild(style);

  const btn = document.createElement("button");
  btn.className = "zj-launcher"; btn.type = "button";
  btn.setAttribute("aria-label", title); btn.textContent = "Chat";

  const iframe = document.createElement("iframe");
  iframe.className = "zj-frame"; iframe.title = title;
  iframe.src = url; iframe.allow = allow; iframe.sandbox = sandbox;

  btn.addEventListener("click", () => {
    const open = iframe.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });

  document.body.appendChild(btn);
  document.body.appendChild(iframe);
})();
Uso en Zajuna
Mostrar siempre los detalles
<script
  src="https://TU-DOMINIO/zajuna-widget.js"
  data-origin="https://TU-DOMINIO"
  data-path-embed="/chat-embed.html"
  data-chat-src="/chat?embed=1"
  data-width="380px"
  data-height="560px"
  data-position="right"
  data-title="Chatbot Tutor Virtual SENA"
  data-avatar="/bot-avatar.png"
  defer
></script>
________________________________________
13) (Opcional) Web Component — public/zajuna-widget.webc.js
Mostrar siempre los detalles
class ChatbotTutorSena extends HTMLElement {
  constructor() {
    super();
    const root = this.attachShadow({ mode: "open" });

    const origin = (this.getAttribute("origin") || window.location.origin).replace(/\/$/, "");
    const pathEmbed = this.getAttribute("path-embed") || "/chat-embed.html";
    const chatSrc = this.getAttribute("chat-src") || "/chat?embed=1";
    const width = this.getAttribute("width") || "380px";
    const height = this.getAttribute("height") || "560px";
    const title = this.getAttribute("title") || "Chatbot Tutor Virtual";
    const allow = this.getAttribute("allow") || "clipboard-write";
    const sandbox = this.getAttribute("sandbox") || "allow-scripts allow-forms allow-same-origin allow-popups";
    const position = this.getAttribute("position") === "left" ? "left" : "right";

    const url = `${origin}${pathEmbed}?src=${encodeURIComponent(chatSrc)}&w=${encodeURIComponent(width)}&h=${encodeURIComponent(height)}&title=${encodeURIComponent(title)}&avatar=${encodeURIComponent(this.getAttribute("avatar") || "/bot-avatar.png")}`;

    const style = document.createElement("style");
    style.textContent = `
      :host { position:fixed; ${position}:20px; bottom:20px; z-index:9999; }
      .wrap { position:relative; }
      .launcher {
        position:absolute; ${position}:0; bottom:0; width:56px; height:56px;
        border-radius:999px; border:0; background:#2563eb; color:#fff; font-weight:600; cursor:pointer;
        box-shadow:0 10px 20px rgba(0,0,0,.25);
      }
      .frame {
        position:absolute; ${position}:0; bottom:70px; width:${width}; height:${height};
        border:0; border-radius:16px; display:none; background:#fff; box-shadow:0 20px 40px rgba(0,0,0,.25);
      }
      .frame.open { display:block; }
      @media (max-width:480px){ .frame { width:94vw; height:70vh; ${position}:0; } }
    `;

    const wrap = document.createElement("div"); wrap.className = "wrap";

    const btn = document.createElement("button");
    btn.className = "launcher"; btn.type = "button";
    btn.setAttribute("aria-label", title); btn.textContent = "Chat";

    const iframe = document.createElement("iframe");
    iframe.className = "frame"; iframe.title = title;
    iframe.src = url; iframe.allow = allow; iframe.sandbox = sandbox;

    btn.addEventListener("click", () => {
      const open = iframe.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    wrap.appendChild(btn);
    wrap.appendChild(iframe);
    root.appendChild(style);
    root.appendChild(wrap);
  }
}
customElements.define("chatbot-tutor-sena", ChatbotTutorSena);
Uso
Mostrar siempre los detalles
<script src="https://TU-DOMINIO/zajuna-widget.webc.js" defer></script>
<chatbot-tutor-sena
  origin="https://TU-DOMINIO"
  path-embed="/chat-embed.html"
  chat-src="/chat?embed=1"
  width="380px"
  height="560px"
  title="Chatbot Tutor Virtual SENA"
  avatar="/bot-avatar.png"
></chatbot-tutor-sena>
________________________________________
14) Autenticación hoy y transición a SSO/OIDC (futuro)
•	Hoy: JWT HS256; access=60min, refresh=7d en cookie httpOnly (SameSite=Lax, Secure en prod).
•	Futuro (SSO/OIDC): Zajuna como IdP → entrega ID Token; el backend valida iss/aud/kid y emite JWT local.
El widget no cambia; solo el flujo de inicio de sesión del admin.
________________________________________
15) Colecciones Mongo (mapeo rápido)
•	users: email (unique), role, token_version, login_failed_count, locked_until, active, created_at, updated_at
•	admin_refresh_tokens: token_hash, expires_at (TTL), revoked, user_id
•	admin_password_resets: token_hash, email, expires_at (TTL), used
•	intents: name, examples[], utter_response, updated_by, updated_at
•	logs: user_id/anon_id, message, intent, confidence, response, entities, timestamp, meta
•	statistics: date, sessions, resolved_rate, fallback_rate, p95_latency
•	support_incidents: reporter, description, status, created_at, updated_at, conversation_ref
Índices
•	users.email (unique); TTL en admin_refresh_tokens.expires_at y admin_password_resets.expires_at;
•	logs (intent, timestamp); support_incidents (status, created_at).
________________________________________
16) Smoke test
•	Dev: npm run dev → abrir http://localhost:5173/chat y enviar un mensaje.
•	Embed: http://localhost:5173/chat-embed.html?src=/chat%3Fembed%3D1.
•	Launcher externo: pegar el snippet del 3.2 en una página simple y verificar:
o	Botón visible, abre panel con iframe.
o	data-badge="auto" muestra no leídos.
o	Handshake de auth:needed → auth:token o redirect a login.
________________________________________
17) Problemas comunes
•	Errores JSX/TSX → usar snippets con entidades HTML.
•	Iframe no carga → revisar CSP/FRAME_ANCESTORS y EMBED_ALLOWED_ORIGINS.
•	401/403 → el host debe enviar token (auth:token) o habilitar modo anónimo.
•	Badge no aparece → data-badge="auto" + revisar postMessage + allowed-origins.
________________________________________
18) Checklist Producción
•	✅ DNS público (HTTPS) del chatbot.
•	✅ CSP frame-ancestors y CORS ALLOWED_ORIGINS con dominios externos.
•	✅ FRONTEND_SITE_URL sirve chat-embed.html y assets.
•	✅ .env frontend: transporte (rest/ws) y URLs.
•	✅ Handshake de login probado.
•	✅ Telemetría básica y plan de roll back.


