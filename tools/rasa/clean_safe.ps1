Write-Host "=== Limpieza segura de Docker + Modelos de Rasa ===" -ForegroundColor Cyan

# 1) Limpieza de imágenes dangling
Write-Host "→ Borrando imágenes dangling (sin etiqueta)..." -ForegroundColor Yellow
docker image prune -f

# 2) Limpieza de cache de Docker
Write-Host "→ Borrando caché de build de Docker..." -ForegroundColor Yellow
docker builder prune -f

# 3) Limpieza de modelos viejos de Rasa (dejando 3 más recientes)
$modelsPath = "rasa\models"
Write-Host "→ Revisando modelos en $modelsPath ..." -ForegroundColor Yellow

if (Test-Path $modelsPath) {
    $files = Get-ChildItem $modelsPath -Filter "*.tar.gz" | Sort-Object LastWriteTime -Descending

    if ($files.Count -le 3) {
        Write-Host "Solo hay $($files.Count) modelos, no se borra nada." -ForegroundColor Green
    } else {
        $toDelete = $files | Select-Object -Skip 3
        foreach ($f in $toDelete) {
            Write-Host "Borrando $($f.Name)" -ForegroundColor Red
            Remove-Item $f.FullName -Force
        }
        Write-Host "✅ Limpieza de modelos completa (se conservaron los 3 más recientes)." -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ No se encontró la carpeta $modelsPath" -ForegroundColor Red
}

Write-Host "=== Limpieza finalizada ===" -ForegroundColor Cyan