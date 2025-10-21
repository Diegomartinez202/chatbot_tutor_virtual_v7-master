<#  ============================================================================
  Full Rasa Cycle (build profile)
  - Levantar servicios
  - Validar datos
  - Entrenar modelo
  - Reiniciar Rasa para aplicar el modelo
  - Pruebas de conversación por REST
  - Logs útiles

  Requisitos:
    - Docker Desktop
    - docker compose en PATH
    - Puertos 5005 (Rasa) y 5055 (Action server) libres en host
============================================================================ #>

$ErrorActionPreference = "Stop"

function Write-Section($title) {
  Write-Host ""
  Write-Host "=== $title" -ForegroundColor Cyan
}

function Wait-HTTPOk($url, $timeoutSec=60) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
    try {
      $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
      if ($r.StatusCode -eq 200) { return $true }
    } catch { Start-Sleep -Seconds 2 }
  }
  return $false
}

function RestSend($sender, $text, $meta=$null) {
  $body = @{ sender = $sender; message = $text }
  if ($meta) { $body["metadata"] = $meta }
  $json = $body | ConvertTo-Json -Depth 5
  $resp = Invoke-RestMethod -Uri "http://localhost:5005/webhooks/rest/webhook" `
                            -Method Post -ContentType "application/json" `
                            -Body $json
  Write-Host "→ [$sender] $text" -ForegroundColor Yellow
  if ($resp) {
    foreach ($m in $resp) {
      if ($m.text) { Write-Host "  ← $($m.text)" -ForegroundColor Green }
      if ($m.custom) { Write-Host ("  ← (custom) " + ($m.custom | ConvertTo-Json -Depth 5)) -ForegroundColor DarkGreen }
      if ($m.buttons) { Write-Host ("  ← (buttons) " + ($m.buttons | ConvertTo-Json -Depth 5)) -ForegroundColor DarkGreen }
    }
  } else {
    Write-Host "  (sin respuesta)" -ForegroundColor DarkYellow
  }
}

# 0) Mostrar versiones rápidas
Write-Section "Versión de compose / entorno"
docker compose version

# 1) Levantar stack (perfil build)
Write-Section "Levantando servicios (perfil build)"
docker compose --profile build up -d

# 2) Health checks
Write-Section "Esperando /status de Rasa"
if (-not (Wait-HTTPOk "http://localhost:5005/status" 120)) {
  throw "Rasa no respondió en /status"
}
Write-Host (Invoke-RestMethod http://localhost:5005/status | ConvertTo-Json -Depth 5)

Write-Section "Esperando /health del Action Server"
if (-not (Wait-HTTPOk "http://localhost:5055/health" 60)) {
  throw "Action Server no respondió en /health"
}
Write-Host (Invoke-RestMethod http://localhost:5055/health | ConvertTo-Json -Depth 5)

# 3) Validar datos
Write-Section "Validando datos (domain + data)"
docker compose exec rasa rasa data validate --domain /app/domain.yml --data /app/data

# 4) Entrenar modelo
Write-Section "Entrenando modelo"
docker compose exec rasa rasa train --domain /app/domain.yml --data /app/data --config /app/config.yml

# 5) Reiniciar Rasa para cargar el nuevo modelo (más simple que PUT /model)
Write-Section "Reiniciando contenedor de Rasa para aplicar el modelo nuevo"
docker compose restart rasa

# Esperar a que suba de nuevo
if (-not (Wait-HTTPOk "http://localhost:5005/status" 120)) {
  throw "Rasa no volvió a responder en /status tras el restart"
}
Write-Host "Rasa OK tras restart." -ForegroundColor Green

# 6) Pruebas automatizadas

Write-Section "Prueba: SALUDO"
RestSend -sender "test-1" -text "hola"

Write-Section "Prueba: SOPORTE (form)"
RestSend -sender "test-2" -text "tengo un problema técnico"
RestSend -sender "test-2" -text "Juan Pérez"
RestSend -sender "test-2" -text "juan@example.com"
RestSend -sender "test-2" -text "La plataforma me muestra pantalla en blanco"

Write-Section "Prueba: RECOVERY (form)"
RestSend -sender "test-3" -text "necesito recuperar mi contraseña"
RestSend -sender "test-3" -text "alumno@zajuna.edu"

Write-Section "Prueba: AUTH GATING (sin auth)"
RestSend -sender "test-4" -text "estado estudiante"

Write-Section "Prueba: AUTH GATING (con auth)"
$meta = @{ auth = @{ hasToken = $true } }
RestSend -sender "test-5" -text "estado estudiante" -meta $meta

Write-Section "Prueba: SOPORTE DIRECTO (sin form con payload embebido)"
# OJO: escapar comillas para JSON embebido en el intent
$payload = '/enviar_soporte{"nombre":"Carlos Test","email":"carlos@test.com","mensaje":"No puedo abrir el curso"}'
RestSend -sender "test-6" -text $payload

# 7) Logs de referencia
Write-Section "Últimos logs (rasa)"
docker compose logs --tail=120 rasa

Write-Section "Últimos logs (action-server)"
docker compose logs --tail=120 action-server

Write-Section "CICLO COMPLETO OK ✅"