🧪 QA Backend – Chatbot Tutor Virtual

Este documento guía la validación del backend (FastAPI + MongoDB + Rasa + Action Server).
Sirve para tu informe técnico: puedes completar la columna Resultado con capturas o notas.

📋 Checklist de pruebas
#	Área	Comando / Acción	Resultado esperado	Resultado
1	Arranque Backend	uvicorn backend.main:app --reload --port 8000 (local) ó docker compose --profile build up backend-dev	Servidor iniciado sin errores	
2	Health API	GET http://localhost:8000/health	{ "ok": true }	
3	Swagger Docs	GET http://localhost:8000/api/docs	Se abre interfaz Swagger UI	
4	Chat Health	GET http://localhost:8000/api/chat/health	{ "ok": true }	
5	Chat POST	```powershell Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/chat
 -Body (@{sender="qa1";message="hola"}	ConvertTo-Json) -ContentType "application/json" ```	Respuesta con intent reconocido y texto del bot
6	Rasa Status	GET http://localhost:5005/status	JSON con versión de Rasa	
7	Action Server	GET http://localhost:5055/health	{ "status": "ok" }	
8	Mongo Conexión	Revisar logs backend (docker compose logs -f backend-dev)	Mensaje: “Connected to MongoDB”	
9	Crear Intent (API)	POST /api/intents con JSON { "name":"qa_test", "examples":["hola qa"] }	201 Created y guardado en Mongo	
10	Listar Intents	GET /api/intents	JSON con intents existentes (incluye qa_test)	
11	Auth Gating (sin token)	POST a /api/chat con intent protegido	Bot responde con utter_need_auth	
12	Auth Gating (con token)	POST con Authorization: Bearer <jwt>	Bot responde flujo privado habilitado	
13	Logs	GET /api/logs	JSON con conversaciones y metadata (request-id, user-agent, etc.)	
14	Rate limit	Hacer >60 requests/min a /api/chat	Devuelve 429 Too Many Requests	
15	Export CSV	GET /api/export	Descarga archivo CSV con logs	
16	Soporte / Tickets	Enviar “necesito soporte” al chat	Ticket registrado en backend vía webhook	
📌 Notas adicionales

Usa check_health.ps1 para validar los tres servicios en un solo paso.

Usa scripts/tasks.ps1 -Profile build -Rebuild para levantar todo rápido.

Si hay fallos, documenta logs de backend y Rasa (útil en el informe).