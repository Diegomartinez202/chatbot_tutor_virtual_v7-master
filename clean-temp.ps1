Write-Host "============================================="
Write-Host " LIMPIEZA DE TEMPORALES Y CACHES - INICIANDO "
Write-Host "=============================================" -ForegroundColor Cyan

# 1️⃣ Limpieza de cache de pip y Python
Write-Host "Eliminando cache de pip y Python..." -ForegroundColor Yellow
try {
    Remove-Item "$env:LOCALAPPDATA\pip\Cache" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:LOCALAPPDATA\Programs\Python\Python310\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "OK - Cache de pip y Python eliminada."
} catch {
    Write-Host "Advertencia: No se pudo limpiar pip o Python cache." -ForegroundColor Red
}

# 2️⃣ Limpieza de carpetas temporales de Windows
Write-Host "Eliminando archivos temporales del sistema..." -ForegroundColor Yellow
try {
    Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:WINDIR\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "OK - Archivos temporales de Windows eliminados."
} catch {
    Write-Host "Advertencia: Error al limpiar temporales de Windows." -ForegroundColor Red
}

# 3️⃣ Limpieza de caches dentro del proyecto
Write-Host "Eliminando __pycache__ dentro del proyecto..." -ForegroundColor Yellow
try {
    Get-ChildItem -Path "C:\Users\USUARIO\Desktop\chatbot_tutor_virtual_v7.3" -Directory -Recurse -Force |
        Where-Object { $_.Name -eq "__pycache__" } |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
    Write-Host "OK - Carpetas __pycache__ eliminadas."
} catch {
    Write-Host "Advertencia: No se pudieron limpiar todas las carpetas __pycache__." -ForegroundColor Red
}

# 4️⃣ Revisión de archivos grandes en Descargas
Write-Host "Revisando archivos mayores a 100MB en Descargas..." -ForegroundColor Yellow
Get-ChildItem "$env:USERPROFILE\Downloads" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 100MB } |
    Select-Object Name, @{Name="Tamano_MB"; Expression={[math]::Round($_.Length / 1MB,2)}}

Write-Host ""
Write-Host "============================================="
Write-Host " LIMPIEZA COMPLETADA "
Write-Host "=============================================" -ForegroundColor Green
Write-Host "Puedes eliminar manualmente los archivos grandes listados arriba si deseas liberar mas espacio."