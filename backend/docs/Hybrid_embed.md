🧩 README – Implementación del Chatbot Tutor Virtual en Modo Embebido (Flujo Híbrido Seguro)

Este documento describe la arquitectura, seguridad, flujo de autenticación y proceso de integración del Chatbot Tutor Virtual en modo embebido (iframe/script), demostrando que puede incorporarse de forma segura, modular y sin modificar el código de plataformas externas como Zajuna.

La implementación presentada corresponde a la prueba técnica real del sistema, basada en un flujo híbrido host ↔ iframe ↔ backend ↔ Rasa, con restricciones estrictas de seguridad (CSP, sandboxing, origen permitido y postMessage seguro).

📌 1. ¿Qué es el modo “Bot Embebido”?

Es una forma de integrar el chatbot dentro de cualquier plataforma externa mediante:

✔ un iframe aislado,
✔ un widget flotante que actúa como lanzador,
✔ un sistema de autenticación diferida,
✔ y comunicación segura host–iframe mediante postMessage.

El bot puede operar en dos modos:

Modo invitado (guest)

Sin autenticación.

Acceso solo a intents públicos (FAQs, rutas de navegación, preguntas generales).

No requiere token.

Modo autenticado (token)

El host (Zajuna u otro) envía un token al iframe solo cuando un intent lo requiere.

Accede a respuestas sensibles:
estado académico, certificados, tutor asignado, gestión de usuario, etc.

📌 2. Flujo general del Bot Embebido
2.1 Componentes

Host (Zajuna u otra plataforma): controla autenticación y estado del widget.

Widget embebido (zajuna-bubble.js + zajuna-bubble.css):
FAB → ventana flotante → iframe.

Frontend Chat (React/Vite): recibe tokens, valida intents sensibles.

Backend FastAPI: recibe solicitudes del chat con metadata.token.

Rasa NLP: interpreta intents, ejecuta acciones, aplica lógica de autorización.

📌 3. Arquitectura resumida (Mermaid)
flowchart LR
  subgraph HOST [Portal Host (Zajuna u otro)]
    UI[SPA/HTML con iframe] -- auth:token --> IFRAME
    UI <-- auth:request -- IFRAME
  end

  subgraph CHAT [Frontend Chat (embed=1)]
    IFRAME[/chat?embed=1&guest=1/]
  end

  subgraph BACKEND [FastAPI Backend]
    API[/api/chat .../auth/validate/]
  end

  subgraph RASA [Rasa NLU/NLG]
    REST[(webhooks/rest/webhook)]
  end

  IFRAME --> API --> REST
  REST --> API --> IFRAME

📌 4. Secuencia de autenticación híbrida
sequenceDiagram
  autonumber
  participant U as Usuario
  participant H as Host (Zajuna)
  participant C as Chat embebido
  participant B as Backend (FastAPI)
  participant R as Rasa

  U->>H: Abre la página con el widget
  H->>C: Carga iframe (/chat?embed=1&guest=1)
  U->>C: Envía intent sensible (ej: /estado_estudiante)
  C-->>H: auth:request
  H->>U: Mostrar login (modal/redirección Zajuna)
  U->>H: Autentica → obtiene token
  H-->>C: auth:token
  C->>B: Enviar consulta con metadata.token
  B->>R: /webhooks/rest/webhook
  R-->>B: respuesta NLG
  B-->>C: mensaje del bot
  C-->>U: muestra la respuesta

📌 5. Seguridad del modo embebido

El sistema incluye medidas de seguridad robustas, verificadas en esta implementación final:

✔ CSP estrictas (Content-Security-Policy)

frame-ancestors restringe quién puede cargar el chat.

frame-src restringe desde qué host se carga el iframe.

✔ postMessage validado con origen

Cada mensaje entrante verifica el event.origin.

Tokens sólo se aceptan si el origen coincide con los orígenes permitidos.

✔ Sandbox en iframe
sandbox="allow-scripts allow-forms allow-popups"


Evita acceso a storage, navegación, ejecución arbitraria y aislamiento del contenido.

✔ Sin exposición directa de tokens

El token sólo viaja en memoria entre host → iframe.

No se expone en URL, logs ni almacenamiento del iframe.

✔ Restricción total de dominios

En zajuna-bubble.js y en HybridChatWidget.jsx:

const ALLOWED_ORIGINS = [
  "https://zajuna.sena.edu.co",
  "http://localhost:8080",
  "http://localhost:5173"
];

✔ Capa Back-End valida permisos

Si llega un intent sensible y no existe token válido:
→ Rasa responde con utter_need_auth.

📌 6. Archivos utilizados en esta implementación

Incluye los componentes reales empleados en la prueba embebida:

Widget

public/embed/zajuna-bubble.js

public/embed/zajuna-bubble.css

Avatar y estados

public/bot-avatar.png

public/bot-loading.png

Host de prueba (demo incluido en repo)

public/hybrid-host.html

Frontend Chat (React/Vite)

HybridChatWidget.jsx

authBridge.js

HostChatBubble.jsx

Todos estos archivos implementan:

UI flotante,

comunicación segura con token,

minimización/restauración,

filtrado de origen,

cambios flexibles de avatar,

manejo del iframe como “micro-app”.

📌 7. Integración en cualquier plataforma externa

Para integrar este bot en Zajuna o cualquier portal institucional, se requieren dos pasos:

🔧 Paso 1 — Incluir el widget
<link rel="stylesheet" href="https://TU_DOMINIO/embed/zajuna-bubble.css" />

<script src="https://TU_DOMINIO/embed/zajuna-bubble.js"></script>

<script>
  ZajunaBubble.create({
    iframeUrl: "https://TU_DOMINIO/chat?embed=1&guest=1",
    allowedOrigin: "https://zajuna.sena.edu.co",
    position: "bottom-right",
  }).mount();
</script>

🔧 Paso 2 — Emitir token cuando el usuario inicia sesión
window.addEventListener("message", (ev) => {
  if (ev.data?.type === "auth:request") {
    const token = localStorage.getItem("token_zajuna");
    if (token) {
      ev.source.postMessage({ type: "auth:token", token }, ev.origin);
    }
  }
});

📌 8. Resultados de la prueba técnica

La implementación demuestra de forma verificable:

✔ El chatbot sí se puede integrar externamente sin modificar Zajuna.
✔ El widget puede abrir, cerrar, minimizar y persistir estado.
✔ La autenticación híbrida funciona y es segura.
✔ Las CSP correctamente aplicadas impiden embedding no autorizado.
✔ Los tokens sólo se transmiten de manera segura host → iframe.
✔ Los intents sensibles se ejecutan únicamente cuando existe token válido.
✔ La UI se adapta automáticamente a invitados y usuarios autenticados.

En otras palabras:

La integración embebida es 100% viable, segura, modular y confiable.

📌 9. Entorno VANILLA (perfil laboratorio)

Este proyecto incluye un perfil adicional “vanilla” destinado a pruebas rápidas, sin proxy, sin Rasa separado y sin autenticación.

✔ Para pruebas de laboratorio.
✔ No recomendado para producción.
✔ Útil para validación de UI, flujo REST básico y debugging rápido.

Cómo ejecutarlo
docker compose --profile vanilla up -d --build


Servicios incluidos:

Servicio	Descripción
backend-vanilla	FastAPI sin Nginx, puerto directo
chat-vanilla	Frontend React sin restricciones CSP
rasa-lite	Modelo simple empaquetado
mongo (opcional)	almacenamiento mínimo

Este perfil permite validar:

carga del iframe sin CSP,

comunicación postMessage básica,

intents simples,

inspección manual del flujo embed sin la complejidad de DEV o PROD.

📌 10. Conclusión

Esta documentación y su implementación demuestran que:

✅ El Chatbot Tutor Virtual puede integrarse mediante un widget embebido seguro.
✅ La arquitectura híbrida (host ↔ iframe ↔ backend ↔ Rasa) funciona correctamente.
✅ El sistema es escalable, desacoplado y puede coexistir sin modificar Zajuna.
✅ Las medidas de seguridad son sólidas: CSP, sandbox, allowedOrigin, tokens controlados.
✅ El flujo es confiable y adecuado para un despliegue institucional controlado.
📌 11. Aviso institucional

Una vez entregado el proyecto, el manejo, tratamiento, almacenamiento y uso de la información recolectada es responsabilidad del SENA, de acuerdo con los lineamientos institucionales y normativa vigente, dado que este trabajo se realiza bajo la modalidad de Proyecto Productivo I+D como requisito de grado.

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

🌐 Integración Híbrida (Embed Web Estándar)

El chatbot puede integrarse en cualquier sitio web externo sin depender de una plataforma educativa específica.

1️⃣ Inserción en sitios externos
<script src="https://TU_DOMINIO/static/widget/chat-widget.js"
  data-chat-url="/chat-embed.html?embed=1"
  data-allowed-origins="https://miportal.com"
  data-login-url="https://miportal.com/login"
  data-badge="auto"></script>

2️⃣ Seguridad

El widget valida:

origin

source

targetOrigin correcto

Y solo acepta mensajes del dominio autorizado.

Se pueden habilitar accesos privados si el host define:

window.getSessionToken = () => localStorage.getItem("token_app");

3️⃣ Flujo de Mensajería (resumen técnico)

chat:badge → actualiza contador en el host.

chat:visibility → restablece contador cuando el chat se abre.

auth:needed → el iframe solicita token.

auth:token → el host responde.

4️⃣ Resultado final

El widget puede incrustarse en:

portales institucionales,

entornos mixtos,

apps web propias del SENA,

intranets, micrositios o páginas HTML puras.

Todo con un modelo seguro y sin exponer credenciales del usuario.