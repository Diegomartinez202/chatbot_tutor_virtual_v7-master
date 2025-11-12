# Ruta dentro del contenedor Rasa Interactive
$rasaInteractivePath = ".\rasa_interactive\<nombre-del-proyecto>"

# Carpetas a copiar
$dataSource = Join-Path $rasaInteractivePath "data"
$configSource = Join-Path $rasaInteractivePath "config"

# Destinos en tu proyecto
$dataDest = ".\data"
$configDest = ".\config"

Write-Host "🔄 Copiando historias e intents..."
Copy-Item -Path "$dataSource\*" -Destination $dataDest -Recurse -Force
Write-Host "✅ Historias e intents copiados a $dataDest"

Write-Host "🔄 Copiando reglas y configuración..."
Copy-Item -Path "$configSource\*" -Destination $configDest -Recurse -Force
Write-Host "✅ Configuración copiada a $configDest"

Write-Host "🎯 Exportación completada. Ahora puedes reentrenar tu modelo."
