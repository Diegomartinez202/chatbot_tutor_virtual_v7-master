# Script: update-nginx.ps1
# Reinicia Nginx y guarda logs.

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = "logs\update-nginx-$timestamp.log"

if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

"[$(Get-Date)] Reiniciando Nginx..." | Tee-Object -FilePath $logPath -Append
docker restart nginx-dev | Tee-Object -FilePath $logPath -Append

"[$(Get-Date)] Finalizado update-nginx.ps1" | Tee-Object -FilePath $logPath -Append

Read-Host "Proceso terminado. Presiona ENTER para salir"