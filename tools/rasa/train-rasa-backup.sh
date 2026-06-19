#!/bin/bash
set -e

MODEL_DIR="./rasa/models"
BACKUP_DIR="./rasa/models_backup"

# Crear carpeta de backup si no existe
mkdir -p "$BACKUP_DIR"

# Timestamp para el backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Hacer backup de modelos existentes
if [ "$(ls -A $MODEL_DIR 2>/dev/null)" ]; then
    echo "📦 Haciendo backup de modelos existentes..."
    mkdir -p "$BACKUP_DIR/backup_$TIMESTAMP"
    cp -r $MODEL_DIR/* "$BACKUP_DIR/backup_$TIMESTAMP/"
    echo "✅ Backup completado en $BACKUP_DIR/backup_$TIMESTAMP"
else
    echo "⚠️ No se encontraron modelos existentes para backup"
fi

# Validar datos Rasa
echo "=== Validando datos Rasa ==="
docker compose run --rm rasa rasa data validate --fail-on-warning

# Entrenar modelo con logs en tiempo real
echo "📦 Entrenando modelo Rasa con logs en tiempo real..."
docker compose run --rm rasa rasa train --verbose

echo "✅ Entrenamiento completado. Los modelos están en ./rasa/models"
