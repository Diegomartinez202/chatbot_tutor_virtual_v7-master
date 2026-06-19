#!/bin/bash
set -e

# Entrenar modelo
echo "[🚀] Iniciando entrenamiento de Rasa..."
rasa train

# Buscar el modelo más reciente
LATEST_MODEL=$(ls -t models/*.tar.gz | head -n 1)

if [ -z "$LATEST_MODEL" ]; then
  echo "[⚠️] No se encontró modelo nuevo."
  exit 1
fi

echo "[💾] Modelo generado: $LATEST_MODEL"

# Registrar en Mongo
python3 /app/scripts/log_model_train.py "$LATEST_MODEL"
