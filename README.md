## 📎 Integración en sitios externos 
Consulta la guía: [EMBED_GUIDE.md](./EMBED_GUIDE.md)

# 🤖 Chatbot Tutor Virtual v7.3 – Proyecto SENA

Sistema modular e inteligente para orientación académica y soporte en línea de preguntas frecuentes, desarrollado como solución embebible para plataformas educativas como **Zajuna**.  
Utiliza **FastAPI**, **Rasa**, **MongoDB**, **Redis**, **Nginx** y **Docker**.

> ⚠️ **Nota técnica sobre el Panel Administrativo (React/Vite)**  
> El proyecto incluye un panel administrativo (`admin_panel_react`) pensado para:
> - gestión de usuarios/cursos,  
> - visualización de logs y métricas,  
> - configuración avanzada del chatbot.
>
> **Sin embargo, en esta entrega del proyecto académico:**
>
> - El panel **NO se despliega ni se evalúa** como parte del sistema entregado.  
> - **NO se garantiza ni certifica su funcionamiento en producción**, por motivos de:
>   - alcance del trabajo,  
>   - tiempo disponible,  
>   - y consideraciones de seguridad.  
> - El foco de la entrega está en:
>   - Backend FastAPI,  
>   - motor conversacional Rasa + Action Server,  
>   - autosave-guardian (seguridad/autosave, si aplica),  
>   - orquestación Docker y Nginx,  
>   - flujo de chat (REST/WebSocket) y persistencia en MongoDB.
>
> El panel administrativo se documenta únicamente como **mejora futura opcional**, para que un
> mantenedor pueda activarlo, revisarlo o extenderlo en un contexto controlado.

---

![Status](https://img.shields.io/badge/estado-en%20pruebas-blue.svg)
![Licencia](https://img.shields.io/badge/licencia-MIT-brightgreen.svg)
![Chatbot Rasa](https://img.shields.io/badge/Rasa-IA%20Conversacional-purple.svg)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green.svg)
![Panel React](https://img.shields.io/badge/Admin%20Panel-React%2BVite-lightgrey.svg)
![Despliegue](https://img.shields.io/badge/despliegue-Docker%20local%20%2B%20opcional%20Railway-lightgrey.svg)

<p align="center">
  <img src="https://img.shields.io/badge/Proyecto-SENA-008000?style=for-the-badge&logo=github" alt="Proyecto SENA" />
  <img src="https://img.shields.io/badge/Estado-En%20desarrollo%20controlado-blue?style=for-the-badge" alt="Estado" />
  <img src="https://img.shields.io/github/license/Diegomartinez202/chatbot_tutor_virtual_v7?style=for-the-badge" alt="Licencia MIT" />
  <img src="https://img.shields.io/badge/Despliegue-Docker%20Compose-2496ED?style=for-the-badge&logo=docker" alt="Docker" />
</p>

<div align="center">

![GitHub repo size](https://img.shields.io/github/repo-size/Diegomartinez202/chatbot_tutor_virtual_v7?label=Repo%20Size)
![GitHub last commit](https://img.shields.io/github/last-commit/Diegomartinez202/chatbot_tutor_virtual_v7?label=Last%20Commit)
![GitHub issues](https://img.shields.io/github/issues/Diegomartinez202/chatbot_tutor_virtual_v7)
![GitHub license](https://img.shields.io/github/license/Diegomartinez202/chatbot_tutor_virtual_v7)
![GitHub stars](https://img.shields.io/github/stars/Diegomartinez202/chatbot_tutor_virtual_v7?style=social)

</div>

---

# 📘 Proyecto Chatbot Tutor Virtual v7.3

## 🏫 Institución
**Servicio Nacional de Aprendizaje (SENA)**

## 👤 Autor
**Diego Armando Martínez Cano**

## 📅 Versión
v7.3.1 — 2025

---

## 🎯 Alcance de la entrega académica

En esta modalidad de **proyecto productivo / i+D+I como requisito de grado**:

- Se entrega, despliega y **valida funcionalmente** el núcleo del **Chatbot Tutor Virtual**:
  - Backend FastAPI (API del chatbot, lógica de negocio, integración con Rasa y MongoDB),
  - motor conversacional Rasa + Action Server,
  - almacenamiento en MongoDB,
  - orquestación Docker (entornos DEV y PROD),
  - Nginx como reverse proxy,
  - (opcional) autosave-guardian y Redis para rate limiting.

- El **panel administrativo React/Vite** se conserva en el repositorio pero:
  - no se despliega en producción real,
  - no se somete a pruebas formales para esta entrega,
  - se deja registrado como **componente opcional / mejora futura**.

> 📌 **Responsabilidad sobre datos en producción**  
> Una vez el sistema sea desplegado y operado con datos reales por el SENA u otra institución,  
> la **responsabilidad sobre el uso de los datos, su protección y explotación** recae en la entidad que lo implemente,  
> de acuerdo con sus políticas internas y la normativa vigente de protección de datos.

---

## 🧩 Componentes del Proyecto

| Carpeta / Componente      | Tecnología                | Descripción                                                                                   |
|---------------------------|---------------------------|-----------------------------------------------------------------------------------------------|
| `backend/`                | FastAPI + MongoDB + Redis | API REST del chatbot, autenticación JWT, integración con Rasa, logs, rate limiting           |
| `rasa/`                   | Rasa 3.6                  | Motor conversacional (intents, reglas, stories, dominio, NLU/NLG)                            |
| `rasa_action_server/`     | Rasa SDK                  | Servidor de acciones personalizadas (lógica de negocio avanzada)                             |
| `autosave_guardian/`      | Flask + MongoDB           | Servicio auxiliar para autosaves / seguridad (si está habilitado en Docker)                  |
| `admin_panel_react/`      | React + Vite              | Panel administrativo (NO incluido en la evaluación; mejora futura opcional)                  |
| `static/widget/`          | HTML + JS                 | Widget web embebible vía `<script>` o `<iframe>`                                             |
| `ops/nginx/`              | Nginx                     | Configuración de Nginx (dev/prod, reverse proxy, TLS y rutas /api, /rasa, /ws, /guardian)    |
| `docker-compose.dev.yml`  | Docker Compose            | Stack **desarrollo**: backend-dev, rasa, action-server, mongo, redis-dev, nginx-dev, etc.    |
| `docker-compose.prod.yml` | Docker Compose            | Stack **producción local/VPS**: backend, rasa, action-server, mongo, redis, nginx-prod, etc. |
| `.github/workflows/`      | GitHub Actions            | Workflows CI/CD (incluyendo despliegue opcional en Railway)                                  |
| `scripts/`                | Bash / PowerShell         | Automatización de tareas: creación de venvs, health checks, entrenamiento de Rasa, etc.      |
| `.env.local`              | ENV Docker local          | Variables comunes para servicios Docker (Mongo, JWT, Rasa, Redis, CORS, etc.)                |
| `.env.root.dev/.prod`     | ENV raíz                  | Indican modo DEV/PROD y el `.env` del backend a utilizar (`BACKEND_ENV_FILE`)                |
| `switch-env.ps1`          | PowerShell                | Script para alternar entre **dev** y **prod** sin borrar `.env.local`                        |

---

## 📂 Estructura del Proyecto (simplificada)

```bash
chatbot_tutor_virtual_v7.3/
├── backend/                    # FastAPI + conexión a MongoDB
├── rasa/                       # Configuración Rasa (nlu.yml, domain.yml, stories.yml, rules.yml)
├── rasa_action_server/         # Custom actions de Rasa
├── autosave_guardian/          # Servicio de autosave / seguridad (opcional)
├── admin_panel_react/          # Panel administrativo React (no evaluado en esta entrega)
├── static/widget/              # Widget embebible (JS/HTML)
├── ops/nginx/                  # Configuración Nginx (dev/prod)
│   ├── nginx.dev.conf
│   ├── nginx.prod.conf
│   └── conf.d/
├── docker-compose.dev.yml      # Orquestación entorno desarrollo
├── docker-compose.prod.yml     # Orquestación entorno producción local/VPS
├── .env.local                  # Configuración común Docker (Mongo, JWT, Rasa, Redis, etc.)
├── .env.root.dev               # Modo raíz desarrollo (MODE=dev, BACKEND_ENV_FILE=backend/.env.dev)
├── .env.root.prod              # Modo raíz producción (MODE=prod, BACKEND_ENV_FILE=backend/.env.production)
├── switch-env.ps1              # Script para alternar entre dev/prod
├── README.md                   # Este documento (institucional)
├── README-dev.md               # Guía técnica para desarrollo local
├── README-deploy.md            # Guía de despliegue DEV/PROD con Docker
├── README-docker.md            # Chuleta de comandos Docker
├── README-railway.md           # (opcional) despliegue de referencia en Railway
└── EMBED_GUIDE.md              # Guía para integración embebida en otros sitios
📌 Introducción
El Chatbot Tutor Virtual es una solución tecnológica diseñada para apoyar a los aprendices del SENA en:

la interacción con la plataforma Zajuna,

la gestión de procesos académicos y administrativos frecuentes,

la resolución rápida de dudas mediante un asistente conversacional embebible.

El proyecto combina:

🤖 IA Conversacional con Rasa (NLU/NLG en español),

⚙️ Backend FastAPI con persistencia en MongoDB y control de acceso por JWT,

🧱 Docker Compose para orquestar backend, Rasa, Mongo, Redis y Nginx,

💬 Widget embebible para integrarse en plataformas externas (como Zajuna),

🔐 Mecanismos de seguridad (rate limiting, CORS, CSP, JWT, autosave-guardian opcional).

El panel administrativo React/Vite está presente en el código pero fuera del alcance evaluado en esta entrega.

🎯 Objetivos
Objetivo General
Desarrollar un Chatbot Tutor Virtual que facilite el acompañamiento académico, mejore la experiencia de los aprendices en la plataforma Zajuna y optimice los procesos de soporte mediante un asistente conversacional embebido y gestionado desde un backend seguro.

Objetivos Específicos
Levantar requerimientos funcionales y no funcionales orientados a soporte académico.

Diseñar una arquitectura modular y escalable basada en microservicios ligeros.

Implementar el backend en FastAPI con autenticación JWT y conexión a MongoDB.

Integrar Rasa para flujos conversacionales inteligentes (intents, reglas, forms, acciones).

Construir un widget web embebible (iframe/script) para sistemas externos.

Incorporar mecanismos de seguridad: rate limit, CORS, CSP y autosave-guardian.

Contenerizar el sistema con Docker Compose para entornos DEV y PROD.

Elaborar documentación técnica, manual de usuario y manual de administración.

Dejar el panel administrativo (admin_panel_react) documentado como mejora futura.

🏗️ Arquitectura General
El sistema incluye:

Backend (FastAPI + MongoDB)

API REST para el chatbot, endpoints /api/chat, /chat, /auth, /health, etc.

Integración con Rasa vía HTTP (REST) y, opcionalmente, WebSocket.

Gestión de usuarios (cuando aplica), logs y configuración básica.

Rasa (NLU/NLG + diálogo)

Intents, entities, stories, reglas y políticas.

Integración con un Action Server para lógica avanzada.

Action Server (Rasa SDK)

Acciones personalizadas en Python: creación de tickets, consultas a APIs externas, etc.

MongoDB

Almacena conversaciones, autosaves y colecciones auxiliares (según configuración).

Redis (en PROD)

Soporta el rate limiting y posibles cachés.

Autosave-Guardian (opcional)

Servicio Flask encapsulado en Docker, expuesto vía /guardian/ mediante Nginx.

Nginx

Reverse proxy único tanto en DEV (nginx-dev) como en PROD (nginx-prod).

Enruta /api hacia backend, /api/chat/rasa/* y /rasa, /ws hacia Rasa, y /guardian hacia autosave-guardian.

Widget Web

Interfaz JS/HTML para embebido en sitios como Zajuna.

Documentado en detalle en EMBED_GUIDE.md.

Panel React (Vite)

Implementado pero no desplegado ni evaluado en esta entrega.

🚀 Despliegue con Docker (resumen)
Detalle completo en:

README-deploy.md → guía paso a paso DEV/PROD

README-docker.md → chuleta rápida de comandos Docker

1️⃣ Entorno de desarrollo (DEV)
powershell
Copiar código
# Marcar modo DEV en el .env raíz
.\switch-env.ps1 dev

# Levantar stack de desarrollo
docker compose -f docker-compose.dev.yml up -d

# Logs principales
docker compose -f docker-compose.dev.yml logs -f backend-dev rasa action-server
Accesos típicos (DEV):

Nginx dev (proxy): http://localhost:8080

Backend directo: http://localhost:8000/docs

Rasa directo: http://localhost:5005/status

El servicio admin-dev (Vite) existe en el compose, pero su uso es opcional y no forma parte de la entrega evaluada.

2️⃣ Entorno de producción local / VPS (PROD)
powershell
Copiar código
# Marcar modo PROD en el .env raíz
.\switch-env.ps1 prod

# Levantar stack de producción
docker compose -f docker-compose.prod.yml up -d

# Logs principales
docker compose -f docker-compose.prod.yml logs -f nginx-prod backend rasa action-server
Accesos típicos (PROD local):

Proxy prod: http://localhost:8080

API vía proxy: http://localhost:8080/api

Rasa vía proxy: http://localhost:8080/rasa

WebSocket: ws://localhost:8080/ws (o wss:// si se configura TLS)

💬 Widget Embebido (vista general)
El widget se integra en plataformas externas (por ejemplo, Zajuna) con:


<script src="https://TU_DOMINIO/static/widget/embed.js"></script>
O mediante un iframe:

<iframe
  src="https://TU_DOMINIO/static/widget/widget.html"
  width="400"
  height="600"
></iframe>
Los detalles de configuración (orígenes permitidos, modos de autenticación, parámetros) se describen en:
👉 EMBED_GUIDE.md

🧪 Pruebas Automáticas y QA
Backend (FastAPI):

cd backend
pytest
Rasa:

Entrenamiento: rasa train (local) o docker compose exec rasa rasa train (Docker).

Modo interactivo: rasa interactive (local) o docker compose exec rasa rasa interactive.

Los scripts y comandos de QA más detallados se encuentran en README-dev.md y en el anexo de QA del informe técnico.

📜 Licencia
Este proyecto se distribuye bajo licencia MIT (ver archivo LICENSE).

Una vez desplegado en entornos reales con datos de personas,
la gestión, protección y uso de la información son responsabilidad de la entidad que lo implemente
(por ejemplo, el SENA), de acuerdo con sus políticas internas y la normativa vigente en materia de protección de datos.

🧠 Créditos
Desarrollado por Diego Martínez como solución de tutoría automatizada para aprendices del SENA.

Incluye integración con:

Plataforma Zajuna (como sistema embebible),

Inteligencia conversacional basada en Rasa,

Backend en FastAPI,

Orquestación vía Docker Compose y configuración de Nginx,

Despliegue de referencia en Railway (opcional, documentado aparte en README-railway.md).



Integración Embebida en Zajuna (LMS Moodle)
🚀 Integración embebida (iframe / script) en Zajuna

Este proyecto soporta integración segura y controlada en plataformas externas como Zajuna (basada en Moodle).
La integración se realiza usando un modelo híbrido:

Render estático del widget (/static/widget/)

Canal seguro REST + WebSocket

Restricción de orígenes (CORS / CSP / Frame-Ancestors)

Token opcional firmado (JWT-lite) para sitios externos

🔧 Opciones de integración
1️⃣ Integración por iframe (modo recomendado)

Inserta en Moodle (HTML de un bloque / sección / etiqueta):

<iframe 
   src="https://TU_DOMINIO/static/widget/widget.html"
   width="380"
   height="600"
   style="border:0; border-radius:8px; overflow:hidden;"
   allow="microphone"
></iframe>

2️⃣ Integración por script embebido (widget)
<script src="https://TU_DOMINIO/static/widget/embed.js"></script>
<div id="tutorbot-container"></div>
<script>
  window.TutorBot.init({
      target: "#tutorbot-container",
      baseUrl: "https://TU_DOMINIO",
      theme: "sena",
      welcomeMessage: "Hola, ¿en qué puedo ayudarte?"
  });
</script>

🔐 Seguridad activada en modo embed

CORS restringido
Solo se permite cargar el widget desde dominios registrados:

ALLOWED_ORIGINS=https://zajuna.sena.edu.co,https://*.zajuna.edu.co


Control de <iframe> vía CSP

FRAME_ANCESTORS 'self' https://zajuna.sena.edu.co;


Opcional: tokens de contexto
Si Zajuna algún día quiere pasar info del aprendiz:

window.TutorBot.init({
  token: "JWT_LITE_GENERADO_EN_BACKEND",
});


Rate limit por IP / usuario

Separación completa de cookies / sesiones del LMS

🧪 Pruebas realizadas (validadas)

El widget carga dentro de Moodle sin errores de sandbox.

El WebSocket funciona desde iframe.

El uso de micrófono está permitido por allow="microphone".

Se validó compatibilidad con Safari/Chrome/Firefox.

Se validó que Rasa responda igual dentro y fuera del frame.

📝 Resultado final

✔ El chatbot puede ser embebido en Zajuna de forma segura, estable y con control de orígenes.
✔ Se recomienda la integración por iframe, que aísla el entorno y evita riesgos.
✔ El equipo de TI puede activar más restricciones CSP si lo desea.




 Integración Híbrida (REST + WebSocket + widget)

Basado en el archivo que me enviaste → Informe_técnico_Flujo_híbrido_embed_web.docx

Cópialo al README o crea README-hybrid-embed.md.

📦 Sección para README: Integración Híbrida (REST + WebSocket + Widget Web)

La plataforma soporta un modo híbrido que combina:

Widget visual (HTML/JS)

REST API del backend (/api/chat)

WebSocket para mensajes en tiempo real (/ws)

Integración opcional con acciones de Rasa (slots, intents, seguimiento del diálogo)

🔧 Arquitectura del flujo híbrido
Sitio externo Zajuna   
      ↓ iFrame / Script
      ↓
  Widget embed (HTML/JS)
      ↓ REST
Backend FastAPI  ←→  Rasa Core
      ↓ WS
  Respuestas en tiempo real


Ventajas del modo híbrido:

Menos latencia (WebSocket)

Permite botones, chips, tarjetas enriquecidas

Permite transferencia de archivos (si se autoriza)

Compatible con sandbox de Moodle

🔒 Seguridad del flujo híbrido
Capa	Protección
Widget	Orígenes restringidos (CORS + CSP)
API REST	Rate-limit + token opcional
WebSocket	Validación de origen + path seguro
Rasa	Aislado en docker sin acceso externo
Backend	Sanitización de texto, logs filtrados
🧪 Flujos probados

Envío de texto

Botones + quick replies

Carruseles

Mensajes de error

Reconexión WebSocket

Flujo fallback / reintentos

📝 Conclusión técnica

✔ El flujo híbrido es apto para producción
✔ Compatible al 100% con Zajuna (Moodle)
✔ Permite total aislamiento entre LMS y chatbot

Perfil VANILLA (implementado pero NO utilizado)

Copiar y pegar:

🧩 Perfil VANILLA (implementado, no utilizado en producción)

Además de los perfiles DEV y PROD, el proyecto incluye un perfil adicional:

🟦 VANILLA

Este perfil está diseñado para:

Laboratorios rápidos

Testing sin build local

Cargar imágenes oficiales desde Docker Hub

Ejecutar solo backend + rasa + action-server sin panel administrativo

🔧 ¿Qué servicios incluye VANILLA?
Servicio	Estado	Descripción
backend	✔	Usa imagen preconstruida
rasa	✔	Imagen de Rasa publicada
action-server	✔	Imagen rasa-sdk
admin panel	❌ NO incluido	
nginx	❌ NO incluido	
▶️ Activación del perfil VANILLA
docker compose --profile vanilla up

🔍 ¿Para qué sirve?

Para probar la API sin recargar código

Para comparar rendimiento entre build local vs imagen

Para pruebas de QA (sin necesidad de frontend)

Para validación CI/CD mínima

⚠️ Nota

El perfil VANILLA no se utiliza en producción ni en el entorno real del proyecto, pero se conserva para futuros mantenedores.

🧪 ANEXO – Pruebas Automatizadas, Depuración y Alcance Validado (Backend / Rasa)

Este proyecto incluye un conjunto amplio de pruebas automatizadas, orientadas originalmente a cubrir:

seguridad (auth, tokens, headers CSP)

comunicación backend ↔ Rasa

flujo funcional del chat

panel administrativo (React)

Sin embargo, para esta entrega académica:

⚠️ El panel administrativo no hace parte del alcance implementado

Por motivos de:

seguridad,

tiempo disponible,

lineamientos de la propuesta de trabajo,

enfoque en el chatbot conversacional,

se deja claramente establecido que el panel administrativo (React/Vite):

NO fue parte del alcance funcional implementado,

NO se despliega,

NO se evalúa,

y se deja documentado como mejora futura.

Como consecuencia, las pruebas relacionadas con módulos de administración fueron archivadas (no eliminadas), quedando fuera del alcance validado por el proyecto.

✔ 3️⃣ Resumen rápido: qué pruebas se mantienen y cuáles se archivan
🟩 Pruebas que SÍ se mantienen (núcleo del flujo del chatbot)

Estas pruebas corresponden a los objetivos reales del sistema:

Autenticación / Seguridad

test_auth.py

test_auth_errors.py

Flujo del Chat

test_chat.py

test_chat_proxy.py (si aplica)

test_functional_flow.py

Rasa e Intents

test_rasa.py

test_intents.py

Seguridad y headers del modo embebido

test_csp_headers.py

test_embed_redirects.py

Configuración del entorno

test_env_config.py

Logs, métricas y estáticos

test_logs.py

test_stats.py

test_static_mount.py

🟨 Pruebas que NO se incluyen en el alcance (archivadas)

(relacionadas al panel administrativo, no implementado en esta entrega)

Se movieron a:
backend/tests/_archive_admin/

Incluyen:

test_admin.py

test_admin_users.py

test_roles.py

test_profile.py

test_upload_csv.py

test_admin_export_intents.py

test_users.py

test_user_manager.py

test_user_settings_api.py

test_train.py (solo si no se usa el endpoint de entrenar)

🧩 Tabla: Mapeo técnico de las pruebas (QA)
Archivo de Test	Qué Comprueba	Objetivo del Proyecto que Soporta
test_auth.py	Validación de tokens y seguridad	Acceso seguro al chatbot
test_auth_errors.py	Manejo correcto de errores de autenticación	Seguridad y robustez
test_chat.py	Flujo básico del chat	Núcleo funcional del Tutor Virtual
test_chat_proxy.py	Redirección / puente /chat	Integración con el widget embebido
test_functional_flow.py	Escenario end-to-end	Validación integrada del sistema
test_rasa.py	Conectividad con Rasa	Inteligencia conversacional
test_intents.py	Validación de estructura de intents	Calidad del modelo
test_env_config.py	Carga y lectura de variables .env	Portabilidad DEV/PROD
test_csp_headers.py	Cabeceras CSP para embeds	Seguridad al integrarlo en Zajuna
test_embed_redirects.py	Flujos de protección del iframe	Protección del contenido
test_logs.py	Auditoría y logs	Trazabilidad
test_stats.py	Métricas de uso	Evaluación del chatbot
test_static_mount.py	Servir widget/estáticos	Integración embebida

🧩 Integración Embebida (Widget Seguro para Plataformas Externas)

El Chatbot Tutor Virtual incluye un mecanismo seguro de incrustación (embed) compatible con plataformas como Zajuna, LMS externos o portales web institucionales.

✔ Características clave

Comunicación segura iframe ↔ host mediante postMessage.

Validación estricta de orígenes permitidos (CSP + CORS).

Flujo de autenticación mediante token del host (opcional).

Propagación completa de trazabilidad usando X-Request-ID.

Widget desacoplado: no accede a datos del host, solo recibe lo que el host entrega explícitamente.

▶ Cómo se incrusta
<script src="https://TU_DOMINIO/static/widget/chat-widget.js"
  data-chat-url="/chat-embed.html?embed=1"
  data-allowed-origins="https://plataforma.edu"
  data-login-url="https://plataforma.edu/login"
  data-badge="auto"></script>

▶ Seguridad aplicada

Content-Security-Policy restringido a orígenes de confianza.

Validación bidireccional del origin (iframe ↔ host).

Tokens nunca se exponen dentro del iframe:
el host responde únicamente cuando el iframe solicita auth:needed.

Backend ajusta automáticamente metadata.auth.hasToken=true|false.

▶ Conclusión técnica

El sistema está preparado para funcionar como módulo embebible seguro, manteniendo compatibilidad con plataformas educativas o institucionales sin comprometer sesiones o datos del usuario.