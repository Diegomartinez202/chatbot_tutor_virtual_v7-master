#!/bin/bash

echo "ðŸ”„ Esperando que MongoDB y Rasa estÃ©n disponibles..."
sleep 10  # Puedes ajustar este tiempo segÃºn lo que tarden en iniciar

echo "ðŸš€ Iniciando el servidor FastAPI..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000
