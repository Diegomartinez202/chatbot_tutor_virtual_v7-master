# Chatbot Tutor Virtual — Embed (Sustentación)

Esta guía muestra **cómo embeber** el chat del Tutor Virtual como **iframe** y también como **burbuja flotante** (widget “bubble”). Incluye:
- Funcionamiento **sin autenticación** (Rasa directo o proxy abierto)
- Funcionamiento **con autenticación Zajuna** (envío de JWT vía `postMessage`)
- **Sincronización de preferencias** (tema/idioma) desde el iframe → host y viceversa
- **Telemetría** básica (`message_sent`, `message_received`)
- CSP/CORS listos con el middleware `add_cors_and_csp`

---

## 0) Rutas y archivos incluidos

**Frontend (este repo)**
- Chat embebible: `/?embed=1` (renderiza `<ChatPage forceEmbed />`)
- JS de burbuja: `public/zajuna-widget.bubble.sustentacion.js`
- Demos HTML:
  - `public/sustentacion-embed.html` (iframe directo — sin auth)
  - `public/sustentacion-embed-auth.html` (iframe directo — con auth por `postMessage`)
  - `public/sustentacion-embed-bubble.html` (burbuja — sin auth)
  - `public/sustentacion-embed-bubble-auth.html` (burbuja — con auth por `postMessage`)
- Este README: `public/EMBED_SUSTENTACION_README.md`

---

## 1) Backend — requisitos

### 1.1 CORS + CSP unificados

En `backend/main.py`:
```py
from backend.middleware.cors_csp import add_cors_and_csp

app = FastAPI(...)
add_cors_and_csp(app)  # ✅ habilita CORS + CSP dinámicos
