#!/bin/bash

echo "ðŸ¤– Ejecutando pruebas de Rasa..."

# Ir a raÃ­z del proyecto
cd "$(dirname "$0")/.."

# Entrenar Rasa (opcional si ya entrenaste)
cd rasa
rasa train

# Simular un mensaje de prueba al bot si estÃ¡ corriendo
curl -X POST http://localhost:5005/webhooks/rest/webhook \
     -H "Content-Type: application/json" \
     -d '{
           "sender": "test_user",
           "message": "Hola"
         }'

cd ..

