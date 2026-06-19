param( 
  [string]$RasaSvc = "rasa"
)

Write-Host "=== VALIDAR ===" -ForegroundColor Cyan
docker compose exec $RasaSvc rasa data validate --domain /app/domain.yml --data /app/data
if ($LASTEXITCODE -ne 0) {
  Write-Host "❌ Error durante la validación. Abortando..." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "=== ENTRENAR ===" -ForegroundColor Cyan
docker compose exec $RasaSvc rasa train --domain /app/domain.yml --data /app/data --config /app/config.yml
if ($LASTEXITCODE -ne 0) {
  Write-Host "❌ Error durante el entrenamiento. Abortando..." -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "=== REINICIAR CONTENEDOR RASA ===" -ForegroundColor Cyan
docker compose restart $RasaSvc

Start-Sleep -Seconds 5

Write-Host "=== STATUS ===" -ForegroundColor Cyan
curl http://localhost:5005/status

Write-Host "=== PRUEBA: saludo ===" -ForegroundColor Cyan
curl -Method POST http://localhost:5005/webhooks/rest/webhook `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"sender":"u1","message":"hola"}'

Write-Host "=== PRUEBA: certificados (requiere auth_check) ===" -ForegroundColor Cyan
curl -Method POST http://localhost:5005/webhooks/rest/webhook `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"sender":"u1","message":"quiero ver mis certificados"}'

Write-Host "=== PRUEBA: certificados info directa (sin auth) ===" -ForegroundColor Cyan
curl -Method POST http://localhost:5005/webhooks/rest/webhook `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"sender":"u1","message":"ver certificados de ejemplo"}'

Write-Host "=== PRUEBA: soporte (form) ===" -ForegroundColor Cyan
curl -Method POST http://localhost:5005/webhooks/rest/webhook `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"sender":"u1","message":"necesito soporte técnico"}'

Write-Host "✅ Proceso completado correctamente." -ForegroundColor Green