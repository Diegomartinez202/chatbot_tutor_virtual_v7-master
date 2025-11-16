Write-Host "=== Entrenando Rasa ===`n"

# ==============================
# 1. Verificar Docker Desktop
# ==============================
try {
    docker info | Out-Null
    Write-Host "🐳 Docker está corriendo correctamente."
}
catch {
    Write-Host "❌ Docker no está disponible. Abre Docker Desktop y espera a que diga 'Engine running'." -ForegroundColor Red
    exit 1
}

# ==============================
# 2. Verificar contenedor Rasa
# ==============================
$rasaContainer = docker ps --filter "name=rasa" --format "{{.Names}}"

if (-not $rasaContainer) {
    Write-Host "❌ No encontré el contenedor de Rasa corriendo." -ForegroundColor Red
    Write-Host "👉 Intenta levantarlo con: docker compose --profile prod up -d rasa"
    exit 1
}

Write-Host "✅ Contenedor Rasa detectado: $rasaContainer"

# ==============================
# 3. Validar datos (domain, stories, rules, nlu)
# ==============================
Write-Host "`n🔎 Ejecutando: rasa data validate ..."
docker exec -it $rasaContainer rasa data validate

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ La validación de datos FALLÓ. Revisa los errores de rules/stories/domain arriba." -ForegroundColor Red
    Write-Host "   (Arregla esos errores y vuelve a ejecutar el script.)"
    exit 1
}

Write-Host "`n✅ Validación de datos OK. Podemos entrenar el modelo." -ForegroundColor Green

# ==============================
# 4. Ejecutar entrenamiento
# ==============================
Write-Host "`n🚀 Iniciando entrenamiento dentro del contenedor..."
docker exec -it $rasaContainer rasa train

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Entrenamiento completado exitosamente. Modelo guardado en /app/models" -ForegroundColor Green
} else {
    Write-Host "`n❌ Hubo un error durante el entrenamiento de Rasa. Revisa los logs arriba." -ForegroundColor Red
}
