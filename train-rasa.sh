#!/bin/bash
set -e

echo "=== Validando datos Rasa ==="
docker compose run --rm rasa rasa data validate --fail-on-warning

echo "📦 Reentrenando modelo Rasa dentro del contenedor..."
docker compose run --rm rasa rasa train

echo "✅ Entrenamiento completado. Los modelos están en ./rasa/models"