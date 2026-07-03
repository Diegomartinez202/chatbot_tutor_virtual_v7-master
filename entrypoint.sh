#!/bin/sh
# Iniciar Ollama en segundo plano
ollama serve &

# Esperar a que el servidor responda
echo "Esperando a Ollama..."
until curl -s http://localhost:11434/api/tags > /dev/null; do sleep 2; done

echo "Ollama está listo y el modelo tinyllama ya debería estar pre-cargado."

# Mantener el contenedor vivo
wait $!