#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
INTER_DIR="$ROOT_DIR/interactive"
DATA_DIR="$ROOT_DIR/data"

DATE_TAG="$(date +%Y%m%d_%H%M%S)"

declare -A MAP_IN_OUT=(
  ["$INTER_DIR/nlu_interactive.yml"]="$DATA_DIR/nlu/nlu_interactive_$DATE_TAG.yml"
  ["$INTER_DIR/stories_interactive.yml"]="$DATA_DIR/stories/stories_interactive_$DATE_TAG.yml"
  ["$INTER_DIR/rules_interactive.yml"]="$DATA_DIR/rules/rules_interactive_$DATE_TAG.yml"
)

echo "📦 Preparando carpetas destino..."
mkdir -p "$DATA_DIR/nlu" "$DATA_DIR/stories" "$DATA_DIR/rules"

moved_any=false

for SRC in "${!MAP_IN_OUT[@]}"; do
  DST="${MAP_IN_OUT[$SRC]}"
  if [[ -s "$SRC" ]]; then
    echo "➡️  Copiando: $SRC  →  $DST"
    cp -n "$SRC" "$DST" || true
    moved_any=true
  else
    echo "⚠️  No existe o está vacío: $SRC (omitido)"
  fi
done

if [[ "$moved_any" == "true" ]]; then
  echo "🔎 Validando datos..."
  cd "$ROOT_DIR"
  if ! rasa data validate; then
    echo "❌ Validación falló. Revisa los YAML recién copiados."
    exit 1
  fi

  echo "🧠 Entrenando modelo..."
  rasa train

  echo "✅ Listo. Modelos en: $ROOT_DIR/models"
else
  echo "ℹ️ No se movió nada; no hay archivos interactivos con contenido."
fi
