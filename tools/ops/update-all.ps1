# Script: update-all.ps1
# Corre Rasa update y luego Nginx update en orden.

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = "logs\update-all-$timestamp.log"

if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

"[$(Get-Date)] Iniciando actualización completa del stack..." | Tee-Object -FilePath $logPath -Append

# Ejecutar update-rasa
& .\update-rasa.ps1 | Tee-Object -FilePath $logPath -Append

# Ejecutar update-nginx
& .\update-nginx.ps1 | Tee-Object -FilePath $logPath -Append

"[$(Get-Date)] Finalizado update-all.ps1" | Tee-Object -FilePath $logPath -Append

Read-Host "Stack actualizado. Presiona ENTER para salir"