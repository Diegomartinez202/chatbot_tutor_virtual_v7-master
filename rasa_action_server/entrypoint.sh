#!/bin/sh

mkdir -p /app/data

if [ ! -f /app/data/semantic_memory.json ]; then
  echo "[]" > /app/data/semantic_memory.json
fi

exec python -m rasa_sdk \
  --actions actions \
  --port 5055