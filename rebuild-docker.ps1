Write-Host "Limpiando contenedores, imágenes y caché antiguas..." -ForegroundColor Cyan
docker compose down --volumes --remove-orphans
docker system prune -af

Write-Host "Construyendo nuevas imágenes desde cero..." -ForegroundColor Yellow
try {
    docker compose build --no-cache
    Write-Host "Construcción completada correctamente." -ForegroundColor Green
}
catch {
    Write-Host "Ocurrió un error durante la construcción de las imágenes." -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando contenedores..." -ForegroundColor Cyan
docker compose up -d

Write-Host "Todo listo. Verifica el estado con:" -ForegroundColor Green
Write-Host "docker ps" -ForegroundColor White