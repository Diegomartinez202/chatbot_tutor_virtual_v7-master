# ===========================
# 🧹 Limpieza Docker Automática
# Archivo: clean-docker.ps1
# Uso: Ejecutar con clic derecho -> "Run with PowerShell"
# ===========================

Write-Host "🚀 Iniciando limpieza de Docker..."

# 1. Eliminar caché de compilación obsoleta
Write-Host "🧹 Limpiando caché de compilación..."
docker builder prune -f

# 2. Eliminar imágenes obsoletas (no usadas por contenedores)
Write-Host "🧹 Eliminando imágenes obsoletas..."
docker image prune -a -f

# 3. Eliminar contenedores detenidos
Write-Host "🧹 Eliminando contenedores detenidos..."
docker container prune -f

# 4. Eliminar volúmenes huérfanos (no asociados a contenedores)
Write-Host "🧹 Eliminando volúmenes huérfanos..."
docker volume prune -f

# 5. Eliminar redes no utilizadas
Write-Host "🧹 Eliminando redes no utilizadas..."
docker network prune -f

# 6. Mostrar espacio recuperado
Write-Host "✅ Limpieza finalizada. Estado actual:"
docker system df