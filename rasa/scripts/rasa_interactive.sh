#!/usr/bin/env bash
set -euo pipefail

# Carpeta base del proyecto Rasa (ajústala si no estás parado en /rasa)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Dónde guardaremos lo generado por interactive
INTER_DIR="$ROOT_DIR/interactive"
mkdir -p "$INTER_DIR"

echo "🚀 Iniciando Rasa Interactive..."
echo "👉 Al terminar, elige 'Export' y apunta los archivos a:"
echo "   $INTER_DIR/nlu_interactive.yml"
echo "   $INTER_DIR/stories_interactive.yml"
echo "   $INTER_DIR/rules_interactive.yml"
echo

cd "$ROOT_DIR"
rasa interactive

