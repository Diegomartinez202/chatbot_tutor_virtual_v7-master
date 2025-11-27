#!/usr/bin/env bash

echo
echo "==================================="
echo "     🚀 ENTRENAMIENTO DE RASA      "
echo "==================================="
echo

# ==========================================
# 1. Verificar que Docker está disponible
# ==========================================
echo "🔍 Verificando que Docker esté encendido..."

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker no está instalado o no está en el PATH."
  echo "👉 Instala Docker Desktop / Docker Engine y vuelve a intentarlo."
  exit 1
fi

# Probar conexión con el daemon de Docker
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker está instalado, pero el daemon no responde."
  echo "👉 Asegúrate de que Docker Desktop esté en estado 'Engine running'."
  exit 1
fi

echo "🐳 Docker está corriendo correctamente."
echo

# ==========================================
# 2. Verificar contenedor de Rasa
# ==========================================
echo "🔍 Buscando contenedor de Rasa (nombre que contenga 'rasa')..."

RASA_CONTAINER=$(docker ps --filter "name=rasa" --format "{{.Names}}")

if [ -z "$RASA_CONTAINER" ]; then
  echo "❌ No se encontró ningún contenedor 'rasa' corriendo."
  echo "Solución sugerida:"
  echo "  👉 Levanta el servicio con:  docker compose up -d rasa"
  echo "  👉 Luego vuelve a ejecutar: ./train_rasa.sh"
  exit 1
fi

echo "✅ Contenedor detectado: $RASA_CONTAINER"
echo

# ==========================================
# 3. Ejecutar entrenamiento dentro del contenedor
# ==========================================
echo "🚀 Iniciando entrenamiento dentro del contenedor..."
echo "(Este proceso puede tardar varios minutos)"
echo

docker exec -it "$RASA_CONTAINER" rasa train
EXIT_CODE=$?

# ==========================================
# 4. Validar resultado del entrenamiento
# ==========================================
echo

if [ $EXIT_CODE -eq 0 ]; then
  echo "==================================="
  echo "  🎉 Entrenamiento finalizado OK   "
  echo "  📦 Modelo guardado en /app/models"
  echo "==================================="
  exit 0
else
  echo "============================================"
  echo "  ❌ Error durante el entrenamiento de Rasa "
  echo "  🔍 Revisa los logs anteriores en consola  "
  echo "============================================"
  exit $EXIT_CODE
fi
