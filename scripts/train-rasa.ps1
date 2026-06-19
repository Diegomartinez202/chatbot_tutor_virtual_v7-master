# \scripts\train-rasa.ps1

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
Write-Host "  1) Ejecutar: docker compose up -d rasa"
Write-Host "  2) Volver a ejecutar este script: .\scripts\train-rasa.ps1"
exit 1
}

Write-Host "Contenedor detectado: $rasaContainer" -ForegroundColor Green

# ==========================================

# 3. Limpiar caché de Rasa

# ==========================================

Write-Host ""
Write-Host "Limpiando caché interno de Rasa dentro del contenedor..."

docker exec -u 0 $rasaContainer sh -lc "rm -rf /app/.rasa /app/rasa/.rasa || true"

Write-Host "Caché de Rasa eliminado (o no existía)." -ForegroundColor Yellow

# ==========================================

# 4. Limpiar log anterior

# ==========================================

Write-Host ""
Write-Host "Preparando archivo de log..."

if (Test-Path ".\train_log.txt") {
Remove-Item ".\train_log.txt" -Force
}

Write-Host "Log anterior eliminado." -ForegroundColor Yellow

# ==========================================

# 5. Validar proyecto Rasa

# ==========================================

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host " VALIDANDO PROYECTO RASA "
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

docker exec $rasaContainer sh -lc "cd /app/rasa && rasa data validate"

if ($LASTEXITCODE -ne 0) {
Write-Host ""
Write-Host "===================================" -ForegroundColor Red
Write-Host " VALIDACION FALLIDA "
Write-Host " Corrija los errores antes de entrenar "
Write-Host "===================================" -ForegroundColor Red
exit 1
}

Write-Host ""
Write-Host "Validación completada correctamente." -ForegroundColor Green

# ==========================================

# 6. Entrenamiento

# ==========================================

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host " INICIANDO ENTRENAMIENTO "
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Este proceso puede tardar varios minutos."
Write-Host "El resultado se almacenará en train_log.txt"
Write-Host ""

docker exec -e RASA_MAX_CACHE_SIZE=0 $rasaContainer `
    sh -lc "cd /app/rasa && rasa train 2>&1" |
    Tee-Object -FilePath ".\train_log.txt"

# ==========================================

# 7. Resultado final

# ==========================================

if ($LASTEXITCODE -eq 0) {

    Write-Host ""
    Write-Host "===================================" -ForegroundColor Green
    Write-Host "  ENTRENAMIENTO FINALIZADO OK      " -ForegroundColor Green
    Write-Host "  Modelo guardado en:" -ForegroundColor Green
    Write-Host "  /app/rasa/models" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Log generado:" -ForegroundColor Green
    Write-Host "  train_log.txt" -ForegroundColor Green
    Write-Host "===================================" -ForegroundColor Green

}
else {

    Write-Host ""
    Write-Host "===================================" -ForegroundColor Red
    Write-Host "  ERROR DURANTE EL ENTRENAMIENTO   " -ForegroundColor Red
    Write-Host ""
    Write-Host "  Revise:" -ForegroundColor Red
    Write-Host "  train_log.txt" -ForegroundColor Red
    Write-Host "===================================" -ForegroundColor Red

}
