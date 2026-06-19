# 🧪 Smoke Tests — Chatbot Tutor Virtual v7

**Propósito:**  
Validar que los servicios principales (Rasa, Backend, Mongo, Redis, Nginx, Panel Admin) inicien correctamente, respondan en endpoints críticos y mantengan conectividad básica entre sí.

---

## 1️⃣ Prueba de Estado de Contenedores

```bash
docker compose ps
Resultado esperado:
Todos los servicios muestran Up (...) (healthy)
Ejemplo:

mathematica
Copiar código
backend-dev     Up (healthy)
rasa            Up (healthy)
action-server   Up (healthy)
mongo           Up
redis           Up
nginx-dev       Up
admin-dev       Up
2️⃣ Verificar Rasa Local
bash
Copiar código
Invoke-RestMethod http://localhost:5005/status | ConvertTo-Json -Depth 5
Resultado esperado:

json
Copiar código
{
  "model_file": "20251027-150545-staccato-permutation.tar.gz",
  "num_active_training_jobs": 0
}
3️⃣ Probar Respuesta del Chatbot
bash
Copiar código
Invoke-RestMethod -Uri http://localhost:5005/webhooks/rest/webhook -Method POST -ContentType 'application/json' -Body '{"sender":"tester","message":"hola"}' | ConvertTo-Json -Depth 5
Resultado esperado:
Respuesta con texto "Hola! ¿En qué puedo ayudarte hoy?" y lista de botones (Explorar temas, Ingreso a Zajuna, etc.)

4️⃣ Validar Backend API
bash
Copiar código
Invoke-RestMethod http://localhost:8000/health
Esperado:
{"status": "ok"} o similar.

Opcional (autenticación):

bash
Copiar código
Invoke-RestMethod http://localhost:8000/api/docs
Debe mostrar el Swagger UI JSON si el backend está activo.

5️⃣ Comprobar Panel Administrativo
Abrir en navegador:

arduino
Copiar código
http://localhost:5173/
Esperado:
Pantalla de login y conexión con backend (si tienes JWT activo).
Luego:

Dashboard carga sin errores.

Botón “Entrenar Bot” ejecuta /train.

Botón “Cargar Intents” funciona sin 500.

6️⃣ Verificar Nginx Reverse Proxy
Abrir:

arduino
Copiar código
http://localhost:8080
Esperado:
Panel o widget visible desde Nginx.

Importante:
El endpoint del chatbot embebido puede verse así:

bash
Copiar código
http://localhost:8080/api/chat
o

bash
Copiar código
http://localhost:8080/rasa/webhooks/rest/webhook
👉 Si devuelve 404, revisa ops/nginx/conf.d/dev.conf y corrige la ruta proxy_pass.

7️⃣ Revisión de Logs
bash
Copiar código
docker compose logs -f rasa
docker compose logs -f backend
docker compose logs -f action-server
Esperado:
Sin errores críticos (no Traceback, no Connection refused).

8️⃣ Persistencia y MongoDB
Acceder:

bash
Copiar código
docker exec -it mongo mongosh
> use rasa
> db.conversations.countDocuments()
Esperado:
Cuenta mayor a 0 después de conversar.

9️⃣ Redis y Rate Limit
bash
Copiar código
docker exec -it redis redis-cli ping
Esperado:
PONG

🔟 Pruebas finales para sustentación
✅ Frontend responde (5173)

✅ Backend responde (8000)

✅ Rasa responde (5005)

✅ Nginx proxy responde (8080)

✅ Mongo conectado

✅ Redis conectado

✅ Entrenamiento automático (si RASA_AUTOTRAIN=true)

✅ Panel React operativo (login, intents, logs)

💾 Notas finales
Para reiniciar todo limpio:

bash
Copiar código
docker compose down -v
docker compose up --build -d
Ver modelo actual:



docker exec -it rasa bash -lc "ls -lh /app/models"
🧠 Autor: Diego Martínez
📅 Versión: 2025-10-27
🏷️ Proyecto: Chatbot Tutor Virtual Zajuna (v7.x)