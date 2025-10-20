# Limpieza de caché de Windows Update y temporales
# Guarda este archivo como clean_windows.ps1

Write-Host "🧹 Iniciando limpieza segura..." -ForegroundColor Cyan

# 1. Detener servicio de Windows Update
Write-Host "⏹ Deteniendo servicio de Windows Update..." -ForegroundColor Yellow
Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
Stop-Service bits -Force -ErrorAction SilentlyContinue

# 2. Borrar caché de Windows Update
Write-Host "🗑 Borrando caché de Windows Update..." -ForegroundColor Yellow
Remove-Item -Path "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "C:\Windows\SoftwareDistribution\DataStore\*" -Recurse -Force -ErrorAction SilentlyContinue

# 3. Borrar archivos temporales del sistema
Write-Host "🗑 Borrando temporales de Windows..." -ForegroundColor Yellow
Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 4. Borrar temporales del usuario actual
Write-Host "🗑 Borrando temporales del usuario..." -ForegroundColor Yellow
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue

# 5. Borrar logs de actualización
Write-Host "🗑 Borrando logs de actualización..." -ForegroundColor Yellow
Remove-Item -Path "C:\Windows\Logs\WindowsUpdate\*" -Recurse -Force -ErrorAction SilentlyContinue

# 6. Reiniciar servicios
Write-Host "▶️ Reiniciando servicio de Windows Update..." -ForegroundColor Yellow
Start-Service wuauserv -ErrorAction SilentlyContinue
Start-Service bits -ErrorAction SilentlyContinue

Write-Host "✅ Limpieza completada. Reinicia el equipo para liberar espacio definitivamente." -ForegroundColor Green