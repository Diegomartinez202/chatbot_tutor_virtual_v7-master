# reset_dev_light.ps1
# Script "light" para reiniciar entorno con Docker Compose
# Ejecuta down + prune + up y luego muestra logs en tiempo real

try {
    Write-Host "[DOWN] Deteniendo y eliminando contenedores..." -ForegroundColor Red
    docker compose --profile build down

    Write-Host "[PRUNE] Limpiando recursos huérfanos (volúmenes, redes, imágenes dangling)..." -ForegroundColor Yellow
    docker system prune -f --volumes

    Write-Host "[UP] Reconstruyendo y levantando contenedores (perfil build)..." -ForegroundColor Green
    docker compose --profile build up --build -d

    Write-Host "`n[LOGS] Mostrando logs en tiempo real (Ctrl+C para salir):" -ForegroundColor Cyan
    docker compose --profile build logs -f
}
catch {
    Write-Host "❌ Error ejecutando reset_dev_light.ps1: $_" -ForegroundColor Red
    exit 1
}
