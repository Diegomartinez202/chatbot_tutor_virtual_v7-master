# ⚠️ Nota técnica sobre el Panel Administrativo (React/Vite)

El proyecto incluye un panel administrativo (`admin_panel_react`) pensado para:

- gestión de usuarios/cursos,  
- visualización de logs y métricas,  
- configuración avanzada del chatbot.

**Sin embargo, en esta entrega del proyecto académico:**

- El panel **NO se despliega ni se evalúa** como parte del sistema entregado.
- **NO se garantiza ni certifica su funcionamiento en producción**, por motivos de:
  - alcance del trabajo,  
  - tiempo disponible,  
  - y consideraciones de seguridad.
- El foco de la entrega está en:
  - Backend FastAPI,  
  - motor conversacional Rasa + Action Server,  
  - orquestación Docker y Nginx,  
  - flujo de chat (REST/WebSocket) y persistencia en MongoDB.

El panel administrativo se deja documentado únicamente como **mejora futura opcional**, para que un
mantenedor pueda activarlo, revisarlo o extenderlo en un contexto controlado y fuera del alcance de la presente evaluación.

---

# Frontend (Admin Panel React + Vite)

> 📌 **Este documento se considera un ANEXO TÉCNICO NO EVALUADO**.  
> Describe cómo arrancar el panel admin **solo con fines de prueba/desarrollo**, bajo responsabilidad del equipo técnico que lo utilice.

---

## 1. Prerrequisitos

- Node.js LTS (con `npm`). Verifica:
  ```bash
  node -v
  npm -v
Backend FastAPI operativo en http://127.0.0.1:8000
(o ajusta la URL según tu entorno).

2. Ejecutar en desarrollo (sin Docker)
bash
Copiar código
cd admin_panel_react
npm install
npm run dev
La aplicación quedará disponible en:

👉 http://localhost:5173

3. Archivo .env (Vite)
Crea el archivo admin_panel_react/.env (para desarrollo local) con lo mínimo:

ini
Copiar código
VITE_API_BASE=http://127.0.0.1:8000
# Opcional, si en el futuro se integra SSO:
# VITE_ZAJUNA_SSO_URL=https://tu-sso.local/oauth/authorize
Si más adelante se usa el panel detrás de Nginx (por ejemplo /api en http://localhost:8080), se podría ajustar a:

ini
Copiar código
VITE_API_BASE=http://localhost:8080/api
(esto ya queda fuera del alcance de la entrega actual y sería tarea del mantenedor futuro).

4. CORS en FastAPI
Para que el panel cargue sin errores de CORS, el backend debe permitir:

http://localhost:5173

http://127.0.0.1:5173

En los .env del backend (por ejemplo backend/.env.dev y/o .env.production) deben estar incluidos en:

env

ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:8080"]
EMBED_ALLOWED_ORIGINS=["'self'","http://localhost:5173","http://localhost:8080"]
FRAME_ANCESTORS=["'self'","http://localhost:8080","http://localhost:5173"]
⚠️ Importante: estos ajustes CORS sí forman parte del sistema principal porque afectan al chat embebido y al frontend público, aunque el panel admin no se utilice.

5. Integración detrás de nginx-dev (opcional)
En el entorno de desarrollo (docker-compose.dev.yml):

El servicio admin-dev expone Vite en el puerto 5173.

nginx-dev actúa como proxy en http://localhost:8080, enviando:

las rutas /api/ al backend,

las rutas /rasa/ y /ws/ a Rasa,

y el resto (/) al frontend React.

Esto permite que, de forma opcional, el panel pueda probarse a través de Nginx con rutas más cercanas a producción, pero no es necesario para la entrega del chatbot.

6. Consideraciones de seguridad y alcance
No se recomienda exponer el panel administrativo a Internet sin:

autenticación robusta,

revisión de roles y permisos,

endurecimiento de cabeceras de seguridad (CSP, X-Frame-Options, etc.).

En este proyecto académico:

No se realiza hardening completo del panel.

No se revisa en detalle la gestión de sesiones ni autorización.

No se hacen pruebas de carga ni pentesting sobre el panel.

Por todo lo anterior, el panel se deja claramente fuera del alcance de la entrega evaluada, y se documenta solo como opción futura de ampliación para el sistema de Tutor Virtual.