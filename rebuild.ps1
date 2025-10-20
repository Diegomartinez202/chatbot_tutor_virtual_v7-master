# rebuild.ps1
# Script para reiniciar limpio el entorno de Docker Compose

Write-Host "[STOP] Deteniendo y eliminando contenedores y volúmenes..." -ForegroundColor Yellow
docker compose down -v

Write-Host "[BUILD] Reconstruyendo imágenes y levantando contenedores en segundo plano..." -ForegroundColor Green
docker compose up -d --build

Write-Host "[STATUS] Estado actual de los servicios:" -ForegroundColor Cyan
docker compose ps

Write-Host "[DONE] Entorno reiniciado correctamente." -ForegroundColor Green