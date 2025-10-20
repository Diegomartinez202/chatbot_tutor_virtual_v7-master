#!/bin/bash
# ===========================
# 🧹 Limpieza Docker Automática
# Archivo: clean-docker.sh
# Uso: ./clean-docker.sh
# ===========================

echo "🚀 Iniciando limpieza de Docker..."

# 1. Eliminar caché de compilación obsoleta
echo "🧹 Limpiando caché de compilación..."
docker builder prune -f

# 2. Eliminar imágenes obsoletas (no usadas por contenedores)
echo "🧹 Eliminando imágenes obsoletas..."
docker image prune -a -f

# 3. Eliminar contenedores detenidos
echo "🧹 Eliminando contenedores detenidos..."
docker container prune -f

# 4. Eliminar volúmenes huérfanos (no asociados a contenedores)
echo "🧹 Eliminando volúmenes huérfanos..."
docker volume prune -f

# 5. Eliminar redes no utilizadas
echo "🧹 Eliminando redes no utilizadas..."
docker network prune -f

# 6. Mostrar espacio recuperado
echo "✅ Limpieza finalizada. Estado actual:"
docker system df