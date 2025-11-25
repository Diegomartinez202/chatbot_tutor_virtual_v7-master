📌 README — Chatbot Tutor Virtual del SENA

Versión estable — Proyecto académico institucional

🎯 Descripción General

El Chatbot Tutor Virtual es un asistente conversacional diseñado para apoyar a los aprendices del SENA en modalidad virtual, proporcionando orientación académica, administrativa y técnica mediante interacción natural.
El sistema está construido sobre una arquitectura modular basada en:

Rasa Open Source (NLU + Core)

Action Server (Python)

Backend FastAPI (seguridad, control, trazabilidad)

MongoDB + Redis (persistencia y sesiones)

Widget embebido vía iframe

Docker + Nginx (orquestación y despliegue)

LLM Ollama 3.1 (experimental, solo desarrollo)

El chatbot puede incrustarse fácilmente en plataformas institucionales como Zajuna, cumpliendo lineamientos de seguridad y sin modificar su código interno.

🏗 Arquitectura del Sistema
Frontend (widget)  →  Backend FastAPI  →  Rasa (NLU/Core)
                            ↓
                       Action Server
                            ↓
                       MongoDB / Redis
                            ↓
                     Ollama (solo dev)


El sistema está dividido en microservicios contenerizados con Docker Compose y protegidos por Nginx.

⚙️ Requisitos
Desarrollo

Python 3.10+

Node.js LTS

Docker + Docker Compose

Rasa CLI

MongoDB / Redis

Ollama (opcional)

Producción

Docker Engine

Nginx reverse proxy

Variables .env correctamente configuradas

MongoDB instancia segura

📥 Instalación
1. Clonar el repositorio
git clone https://github.com/tu-repo/chatbot-tutor-virtual.git
cd chatbot-tutor-virtual

2. Crear archivos de entorno

Copiar cada .env.example a .env y configurarlo.

3. Ejecutar entorno de desarrollo
docker compose -f docker-compose.dev.yml up --build

4. Entrenar el modelo Rasa
cd rasa
rasa train

🐳 Despliegue en Producción
docker compose -f docker-compose.prod.yml up --build -d


Nginx expondrá el sistema sobre el puerto 80/8080, aplicando:

CORS estrictos

CSP estrictas

control de iframe por frame-ancestors

limitación por dominios

💬 Integración mediante iframe

El chatbot se incrusta en plataformas externas mediante:

<iframe 
  src="https://tudominio/chat-embed.html"
  style="width:100%; height:600px; border:none;"
  allow="cross-origin-isolated">
</iframe>


Esta es la única forma autorizada institucionalmente.

🔐 Seguridad

El sistema incorpora:

CORS con orígenes restringidos

CSP configurada desde Nginx

Sanitización de entradas

No almacena datos personales sensibles

No accede directamente a SofíaPlus ni LMS

LLM desactivado en producción

Panel administrativo deshabilitado

Las restricciones provienen del documento institucional:

📄 PROPUESTA_IMPLEMENTACIÓN_EMBEBIDA_CHATBOT_TUTOR_VIRTUAL_ZAJUNA.docx

🚧 Limitaciones Actuales

No integra SSO institucional Zajuna

Panel administrativo no habilitado

LLM activo solo en desarrollo

Entrenamiento únicamente por consola

No accede a sistemas institucionales internos

🚀 Mejoras Futuras

Integración avanzada con APIs académicas

Panel administrativo con roles y permisos

Autenticación federada SSO SENA

Analítica conversacional avanzada

Soporte multicanal (WhatsApp, Telegram, Web institucional)

🛠 Soporte Técnico

Para mantenimiento:
Consultar la Guía de Soporte Técnico incluida en este proyecto.
Incluye:

Diagnóstico rápido

Revisión de contenedores

Logs críticos

Pruebas post–despliegue

Metodología de resolución de incidentes

📜 Licencia

Sugerido:
MIT License – Uso académico y educativo