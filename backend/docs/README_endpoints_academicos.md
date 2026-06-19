# Tutor Virtual Zajuna – Endpoints integrs académicos protegidos

Este documento demuestra que el backend del **Tutor Virtual Zajuna** ya está preparado para integrarse con la plataforma Zajuna mediante:

- Autenticación con JWT.
- Manejo de roles (`admin`, `soporte`, `estudiante`, `usuario`).
- Endpoints académicos protegidos por rol.
- Consumo seguro desde el chatbot (Rasa) usando metadata y tokens.

---

## 1. Arquitectura de autenticación y roles

- Los usuarios se almacenan en MongoDB.
- Al autenticarse, se genera un **JWT** con la siguiente información mínima:

  ```json
  {
    "sub": "<user_id>",
    "email": "usuario@zajuna.edu",
    "rol": "estudiante" | "admin" | "soporte" | "usuario"
  }
Ese token se envía en los endpoints protegidos mediante:

makefile
Copiar código
Authorization: Bearer <token>
Roles y permisos
admin / soporte

Pueden consultar información académica de cualquier user_id.

estudiante

Solo puede ver sus propios datos (coincide user.id con user_id).

usuario (rol del panel)

No tiene acceso a datos académicos (solo panel: logs, estadísticas, etc.).

Esta matriz de permisos se aplica en los endpoints académicos usando get_current_user y validación del campo rol.

2. Endpoints académicos implementados
Los endpoints clave ya implementados son:

GET /api/estado-estudiante

Devuelve el estado académico del usuario autenticado (self).

Respuesta: { "estado": "Activo" } (o valor real desde Mongo).

GET /api/certificados

Devuelve la lista de certificados del estudiante autenticado.

Si no hay datos en Mongo, devuelve una lista demo controlada.

GET /api/horarios

Devuelve horarios del estudiante autenticado desde Mongo.

GET /api/progreso-cursos

Devuelve avance global y progreso por curso del estudiante.

GET /api/usuarios/{user_id}

Devuelve datos del usuario.

Matriz de acceso:

admin/soporte → cualquier user_id.

estudiante → solo su propio user_id.

usuario → sin acceso (403).

GET /api/usuarios/{user_id}/estado

Devuelve el estado académico por usuario.

Misma matriz de roles que en calificaciones.

GET /api/usuarios/{user_id}/calificaciones

Devuelve calificaciones del estudiante desde Mongo.

Misma matriz de roles.

GET /api/tutor

Devuelve tutor asignado del estudiante autenticado.

Solo accesible por admin, soporte o estudiante.

3. Integración con el chatbot (Rasa + widget embebido)
El flujo previsto de integración con Zajuna es:

El estudiante inicia sesión en Zajuna.

Zajuna genera/propaga un token JWT con sub = user_id y rol = "estudiante".

El widget del chatbot embebido envía las consultas a:

POST /chat o POST /api/chat

Incluyendo:

http
Copiar código
Authorization: Bearer <token>
El backend valida el token con get_current_user_optional:

Si hay token → modo estudiante (autenticado).

Si no hay token → modo invitado.

El backend enriquece el metadata que llega a Rasa con:

json
Copiar código
"user": {
  "id": "<user_id> | null",
  "email": "<email> | null",
  "mode": "estudiante" | "invitado"
}
Las acciones personalizadas de Rasa (ActionVerEstadoEstudiante, ActionListarCertificados, ActionConsultarHorariosClases, ActionConsultarProgresoCurso, etc.) leen:

python
Copiar código
metadata = tracker.latest_message.get("metadata", {}) or {}
user_meta = metadata.get("user") or {}
mode = user_meta.get("mode")      # "estudiante" | "invitado"
user_id = user_meta.get("id")
email = user_meta.get("email")
Cuando el usuario está autenticado y mode == "estudiante", la acción llama al backend:

GET /api/estado-estudiante

GET /api/certificados

GET /api/horarios

GET /api/progreso-cursos

Siempre usando el token (_auth_headers(tracker)).

4. Seguridad y modo invitado
Modo invitado:

No tiene token (Authorization vacío).

Puede conversar con el bot, pero NO accede a datos académicos reales.

Las acciones académicas responden con mensajes genéricos + sugerencia de autenticarse.

Modo estudiante autenticado:

Rasa recibe metadata["user"].mode = "estudiante".

Las acciones académicas consumen el backend real protegidas con JWT y roles.

Si el estudiante intenta ver datos de otro user_id, el backend devuelve 403.

5. Pruebas automatizadas (pytest)
Se incluye el archivo:

backend/tests/test_academico_endpoints_real.py

Este archivo valida:

Que los endpoints devuelven datos válidos para un estudiante.

Que usuario (rol de panel) no puede acceder a endpoints académicos.

Que admin/soporte pueden consultar otros user_id.

Que los fallbacks demo funcionan cuando no hay datos en Mongo.

Estas pruebas demuestran que el sistema YA está listo para recibir el token de Zajuna y actuar de forma segura y diferenciada por rol.