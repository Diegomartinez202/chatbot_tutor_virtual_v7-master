# Guía de despliegue con Docker

## 🚢 Requisitos previos
- Docker y Docker Compose instalados.
- Archivo `.env` con las variables necesarias (API, DB).

## ⚙️ Comandos principales
```bash
cd docker
docker-compose up --build       # Levanta todo el sistema
docker-compose down             # Detiene todos los servicios
🌐 Accesos esperados
•	Backend FastAPI: http://localhost:8000
•	Widget embebido: http://localhost:8000/static/widget/
•	Admin Panel React (si se despliega): http://localhost:5173
📦 Servicios que se levantan
•	MongoDB (con datos precargados si usas init-mongo.js)
•	Rasa + Action Server
•	FastAPI con widget embebido
yaml
CopiarEditar

---
