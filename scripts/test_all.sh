#!/bin/bash

echo "Iniciando test general del sistema..."

# Simulación de tests básicos (puedes reemplazar por comandos reales)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ping
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/intents
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/logs

echo "Test finalizado."
