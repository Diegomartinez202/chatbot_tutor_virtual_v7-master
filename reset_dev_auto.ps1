# reset_dev_auto.ps1
# Script automático para reiniciar entorno con Docker Compose
# Ejecuta down + prune + up y termina (sin mostrar logs en tiempo real)

try {
    Write-Host "[DOWN] Deteniendo y eliminando contenedores..." -ForegroundColor Red
    docker compose --profile build down

    Write-Host "[PRUNE] Limpiando recursos huérfanos (volúmenes, redes, imágenes dangling)..." -ForegroundColor Yellow
    docker system prune -f --volumes

    Write-Host "[UP] Reconstruyendo y levantando contenedores (perfil build)..." -ForegroundColor Green
    docker compose --profile build up --build -d

    Write-Host "`n✅ Reset completo. Contenedores levantados en segundo plano." -ForegroundColor Cyan
    Write-Host "   Usa 'docker compose --profile build ps' para ver el estado o 'docker compose --profile build logs -f' para seguirlos." -ForegroundColor DarkGray
}
catch {
    Write-Host "❌ Error ejecutando reset_dev_auto.ps1: $_" -ForegroundColor Red
    exit 1
}