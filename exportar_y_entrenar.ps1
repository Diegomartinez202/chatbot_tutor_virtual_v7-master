# ==============================
# Script todo en uno: Exportar, Validar y Entrenar Rasa
# ==============================

# Cambia esto al nombre exacto de tu proyecto dentro de rasa_interactive
$nombreProyecto = "<nombre-del-proyecto>"

# Rutas dentro de tu proyecto
$rasaInteractivePath = ".\rasa_interactive\$nombreProyecto"
$dataSource = Join-Path $rasaInteractivePath "data"
$configSource = Join-Path $rasaInteractivePath "config"

$dataDest = ".\data"
$configDest = ".\config"

# ------------------------------
# 1️⃣ Copiar historias e intents
# ------------------------------
Write-Host "🔄 Copiando historias e intents..."
Copy-Item -Path "$dataSource\*" -Destination $dataDest -Recurse -Force
Write-Host "✅ Historias e intents copiados a $dataDest"

# ------------------------------
# 2️⃣ Copiar reglas y configuración
# ------------------------------
Write-Host "🔄 Copiando reglas y configuración..."
Copy-Item -Path "$configSource\*" -Destination $configDest -Recurse -Force
Write-Host "✅ Configuración copiada a $configDest"

# ------------------------------
# 3️⃣ Validar datos de Rasa
# ------------------------------
Write-Host "🔍 Validando datos de Rasa..."
docker compose run --rm rasa rasa data validate --debug
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Datos validados correctamente."
} else {
    Write-Host "⚠️ Se encontraron advertencias o errores. Revisa los mensajes anteriores."
}

# ------------------------------
# 4️⃣ Entrenar modelo
# ------------------------------
Write-Host "🚀 Entrenando modelo Rasa..."
docker compose run --rm rasa rasa train
if ($LASTEXITCODE -eq 0) {
    Write-Host "🎯 Modelo entrenado correctamente. Todo listo!"
} else {
    Write-Host "❌ Error al entrenar el modelo. Revisa los mensajes anteriores."
}
