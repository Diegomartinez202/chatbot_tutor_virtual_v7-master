#!/bin/sh
# Iniciar Ollama en segundo plano para poder descargar el modelo
ollama serve &
pid=$!

# Esperar a que el servidor responda
echo "Esperando a Ollama..."
until curl -s http://localhost:11434/api/tags > /dev/null; do sleep 2; done

# Descargar el modelo si no existe
if ! ollama list | grep -q "phi3:mini"; then
    echo "Descargando phi3:mini..."
    ollama pull phi3:mini
fi

# Traer el proceso al frente
wait $pid