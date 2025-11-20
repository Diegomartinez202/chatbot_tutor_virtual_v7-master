# 🙌 Contribuir al Chatbot Tutor Virtual

Gracias por tu interés en contribuir a este proyecto 🎓🤖.

Este sistema fue desarrollado inicialmente como parte de un **proyecto formativo del SENA**, y se publica con fines educativos y de mejora continua. Está orientado a:

- Backend **FastAPI** (API del chatbot)
- Motor conversacional **Rasa** + **Action Server**
- Orquestación con **Docker / Nginx / Mongo / Redis**
- (Opcional) Panel administrativo React/Vite como **mejora futura**

---

## ✅ Requisitos previos

- Conocimientos básicos de:
  - Python (FastAPI, Pydantic, etc.)
  - Rasa 3.x (intents, stories, rules, actions)
  - Docker Compose (para levantar el entorno)
- Herramientas instaladas:
  - Git
  - Python 3.11+
  - Node.js LTS (solo si trabajas con `admin_panel_react`)
  - Docker Desktop (recomendado)

---

## 🧩 Alcance de las contribuciones

En la versión entregada académicamente, el foco está en:

- Lógica de negocio del backend (API, validaciones, seguridad básica).
- Configuración y entrenamiento del bot en Rasa.
- Integración con Action Server y servicios externos (helpdesk, etc.).
- Infraestructura mínima de despliegue (Docker, Nginx, Mongo, Redis).

El **panel administrativo (`admin_panel_react`)**:

- Existe en el código, pero **no forma parte de la entrega evaluada**.
- Puede recibir contribuciones, pero se considera **módulo opcional / mejora futura**.

Si envías mejoras sobre el panel, se agradecerá que lo indiques explícitamente en el título del PR:
`[admin-panel] Descripción de la mejora`.

---

## 🔀 Flujo básico para contribuir

1. **Haz un fork** del repositorio.

2. Crea una nueva rama descriptiva:

   ```bash
   git checkout -b feature/mi-mejora
Realiza tus cambios siguiendo las buenas prácticas:

Mantén la estructura modular (no mezcles backend, Rasa, infra en un mismo commit grande).

No borres lógica de negocio existente sin justificarlo en el PR.

Si tocas .env.example, no añadas credenciales reales.

Añade pruebas si es necesario:

Backend: tests de FastAPI (pytest) o scripts de smoke test.

Rasa: valida datos (rasa data validate) y entrena (rasa train).

Haz commit y push a tu rama:

bash
Copiar código
git commit -m "💡 Mejora: descripción breve"
git push origin feature/mi-mejora
Abre un Pull Request (PR) y describe:

Qué problema resuelves o qué mejora implementas.

Si afecta a despliegue, .env, Nginx u orquestación Docker.

Si toca el panel admin, indícalo claramente (módulo no evaluado).

📦 Estándares de código
Python (backend / actions)
Seguir PEP8 en lo razonable.

Nombres de variables y funciones claros (en inglés o español, pero coherentes).

Manejar errores con try/except donde tenga sentido, sin silenciar excepciones críticas.

Evitar lógica de negocio “quemada” (hardcodear URLs, tokens, etc.).

Rasa
Mantener consistencia en intents, entities y respuestas.

Ejecutar siempre:

bash
Copiar código
rasa data validate
rasa train
antes de subir cambios relacionados al bot.

React (panel admin – opcional)
Usar componentes reutilizables.

Evitar lógica de negocio pesada en el frontend; dejarla en el backend.

No hardcodear URLs de API; usar las variables VITE_*.

🔐 Seguridad y datos sensibles
No subas archivos .env, dumps de bases de datos ni credenciales.

No incluyas información de usuarios reales ni datos personales.

Si propones cambios relacionados con autenticación o tokens:

documenta claramente el flujo,

no uses claves reales en ejemplos.

⚖️ Licencia y responsabilidad
El proyecto se publica bajo licencia MIT (ver archivo LICENSE):

Puedes usar, modificar y redistribuir el código, bajo los términos de dicha licencia.

El software se entrega “tal cual”, sin garantías.

📝 Contexto académico / institucional
Una vez el sistema sea desplegado con datos reales por una entidad (por ejemplo, el SENA),
la responsabilidad sobre el uso y tratamiento de la información recae en dicha entidad,
conforme a la normativa vigente en materia de protección de datos.
Los autores originales no asumen responsabilidades adicionales sobre el tratamiento de datos
que terceros realicen al desplegar o adaptar este software.

❤️ ¡Gracias!
Cualquier contribución —documentación, correcciones menores, mejoras de infraestructura o de diálogo del bot— es bienvenida 🙌.

Si no estás seguro de por dónde empezar, puedes:

Abrir un Issue con tu duda/mejora,

o proponer directamente un pequeño PR con mejoras en documentación o scripts de despliegue.