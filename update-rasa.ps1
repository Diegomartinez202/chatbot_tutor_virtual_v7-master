# Script: update-rasa.ps1
# Copia archivos al contenedor de Rasa, entrena, reinicia y guarda logs.

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = "logs\update-rasa-$timestamp.log"

# Crear carpeta de logs si no existe
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

"[$(Get-Date)] Iniciando actualización de Rasa..." | Tee-Object -FilePath $logPath -Append

# Archivos a copiar
$files = @(
    "rasa\domain.yml",
    "rasa\data\nlu.yml",
    "rasa\data\stories.yml",
    "rasa\data\rules.yml",
    "rasa\config.yml"
)

foreach ($file in $files) {
    $dest = "/app/" + ($file -replace "rasa\\","")
    docker cp $file rasa:$dest | Tee-Object -FilePath $logPath -Append
    "[$(Get-Date)] Copiado $file -> $dest" | Tee-Object -FilePath $logPath -Append
}

# Entrenar modelo
"[$(Get-Date)] Ejecutando rasa train..." | Tee-Object -FilePath $logPath -Append
docker exec rasa rasa train | Tee-Object -FilePath $logPath -Append

# Reiniciar contenedor
"[$(Get-Date)] Reiniciando contenedor Rasa..." | Tee-Object -FilePath $logPath -Append
docker restart rasa | Tee-Object -FilePath $logPath -Append

"[$(Get-Date)] Finalizado update-rasa.ps1" | Tee-Object -FilePath $logPath -Append

Read-Host "Proceso terminado. Presiona ENTER para salir"
