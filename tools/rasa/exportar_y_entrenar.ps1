Param(
    [Parameter(Mandatory=$true)]
    [string]$NombreProyecto,   # nombre dentro de rasa_interactive

    [switch]$SoloExportar      # si se pasa, NO valida ni entrena
)

Write-Host "===============================" -ForegroundColor Cyan
Write-Host "  Exportar y Entrenar Rasa     " -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Rutas dentro de tu proyecto
$rasaInteractivePath = ".\rasa_interactive\$NombreProyecto"
$dataSource   = Join-Path $rasaInteractivePath "data"
$configSource = Join-Path $rasaInteractivePath "config"

$dataDest   = ".\data"
$configDest = ".\config"

if (-not (Test-Path $rasaInteractivePath)) {
    Write-Host "❌ No existe la ruta $rasaInteractivePath" -ForegroundColor Red
    Write-Host "   Asegúrate de que el nombre del proyecto es correcto."
    exit 1
}

# 1) Copiar historias e intents
Write-Host "🔄 Copiando historias e intents..."
Copy-Item -Path "$dataSource\*" -Destination $dataDest -Recurse -Force
Write-Host "✅ Historias e intents copiados a $dataDest"

# 2) Copiar reglas y configuración
Write-Host "🔄 Copiando reglas y configuración..."
Copy-Item -Path "$configSource\*" -Destination $configDest -Recurse -Force
Write-Host "✅ Configuración copiada a $configDest"

if ($SoloExportar) {
    Write-Host "ℹ️ Solo exportación solicitada. No se ejecuta validación ni entrenamiento." -ForegroundColor Yellow
    Write-Host "🎯 Exportación completada."
    exit 0
}

# 3) Validar datos de Rasa
Write-Host "🔍 Validando datos de Rasa..."
docker compose run --rm rasa rasa data validate --debug
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Datos validados correctamente."
} else {
    Write-Host "⚠️ Se encontraron advertencias o errores. Revisa los mensajes anteriores." -ForegroundColor Yellow
}

# 4) Entrenar modelo
Write-Host "🚀 Entrenando modelo Rasa..."
docker compose run --rm rasa rasa train
if ($LASTEXITCODE -eq 0) {
    Write-Host "🎯 Modelo entrenado correctamente. Todo listo!" -ForegroundColor Green
} else {
    Write-Host "❌ Error al entrenar el modelo. Revisa los mensajes anteriores." -ForegroundColor Red
}
