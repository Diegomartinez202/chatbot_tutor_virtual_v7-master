#!/usr/bin/env bash
# Guarda esto y dale permiso de ejecución
set -e
# validar datos
rasa data validate
# entrenar
rasa train
# reiniciar actions (si correspond)
# pm2 restart actions || true
echo "Retrain complete at $(date)"
