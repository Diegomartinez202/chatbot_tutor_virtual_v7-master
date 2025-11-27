Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "     ENTRENAMIENTO DE RASA         "
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================
# 1. Verificar Docker Desktop en ejecución
# ==========================================
Write-Host "Verificando que Docker esté encendido..."

try {
    docker info | Out-Null
    Write-Host "Docker está corriendo correctamente." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Docker no está disponible." -ForegroundColor Red
    Write-Host "Abra Docker Desktop y espere a que diga: 'Engine running'."
    exit 1
}

# ==========================================
# 2. Verificar contenedor de Rasa
# ==========================================
Write-Host ""
Write-Host "Buscando contenedor de Rasa (nombre que contenga 'rasa')..."

$rasaContainer = docker ps --filter "name=rasa" --format "{{.Names}}"

if (-not $rasaContainer) {
    Write-Host "ERROR: No se encontró un contenedor cuyo nombre contenga 'rasa'." -ForegroundColor Red
    Write-Host "Solución sugerida:"
    Write-Host "  1) Ejecutar:  docker compose up -d rasa"
    Write-Host "  2) Volver a ejecutar este script:  .\scripts\train-rasa.ps1"
    exit 1
}

Write-Host "Contenedor detectado: $rasaContainer" -ForegroundColor Green

# ==========================================
# 2.1 Limpiar caché interno de Rasa (SQLite)
# ==========================================
Write-Host ""
Write-Host "Limpiando caché interno de Rasa dentro del contenedor..."

# Borramos posibles caches en ambas rutas que ya detectaste
docker exec $rasaContainer sh -lc "rm -rf /app/.rasa || true"
docker exec $rasaContainer sh -lc "rm -rf /app/rasa/.rasa || true"

Write-Host "Caché de Rasa eliminado (o no existía)." -ForegroundColor Yellow

# ==========================================
# 3. Iniciar entrenamiento dentro del contenedor
# ==========================================
Write-Host ""
Write-Host "Iniciando entrenamiento dentro del contenedor..."
Write-Host "Este proceso puede tardar varios minutos."
Write-Host ""

# Desactivamos el cache de Rasa para evitar el SQLite readonly
docker exec -e RASA_MAX_CACHE_SIZE=0 -it $rasaContainer sh -lc "cd /app/rasa && rasa train"

# ==========================================
# 4. Validación del resultado del entrenamiento
# ==========================================
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===================================" -ForegroundColor Green
    Write-Host "  Entrenamiento finalizado OK      " -ForegroundColor Green
    Write-Host "  Modelo guardado en /app/rasa/models" -ForegroundColor Green
    Write-Host "===================================" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "===================================" -ForegroundColor Red
    Write-Host "  ERROR durante el entrenamiento   " -ForegroundColor Red
    Write-Host "  Revise los mensajes anteriores   " -ForegroundColor Red
    Write-Host "===================================" -ForegroundColor Red
}
