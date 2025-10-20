#!/bin/bash

echo "ðŸš€ Iniciando Chatbot Tutor Virtual..."

# Activar entorno virtual si es necesario (opcional)
# source venv/bin/activate

# Migraciones, precargas o tareas previas (opcional)
# python backend/scripts/preload.py

# Iniciar el servidor Uvicorn con FastAPI
exec uvicorn backend.main:app --host=0.0.0.0 --port=${PORT:-8000}
