<#  smoke-prod.ps1
    Smoke test express de PROD (perfil "prod") para sustentación.
    Realiza:
      1) docker compose ps
      2) Health checks: backend, rasa, nginx
      3) Round-trip de bot vía Nginx → /rasa/webhooks/rest/webhook
      4) Admin SPA 200 OK

    Uso:
      .\smoke-prod.ps1                # test estándar
      .\smoke-prod.ps1 -Open          # abre http://localhost y /docs si pasa
      .\smoke-prod.ps1 -Logs          # muestra logs si algo falla
#>

param(
  [switch]$Open,
  [switch]$Logs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host "== Smoke PROD | carpeta: $repoRoot ==" -ForegroundColor Cyan

# Perfil sólo para esta ejecución
$env:COMPOSE_PROFILES = "prod"

function Try-Command {
  param(
    [scriptblock]$Cmd,
    [string]$Name,
    [int]$Retries = 10,
    [int]$DelaySec = 3
  )
  for ($i=1; $i -le $Retries; $i++) {
    try {
      $res = & $Cmd
      Write-Host "✔ $Name OK" -ForegroundColor Green
      return @{ ok = $true; res = $res }
    } catch {
      Write-Host "… esperando $Name ($i/$Retries)" -ForegroundColor DarkYellow
      Start-Sleep -Seconds $DelaySec
    }
  }
  Write-Host "✖ $Name FALLÓ" -ForegroundColor Red
  return @{ ok = $false; res = $null }
}

$allOk = $true

# 1) PS servicios
try {
  $psOut = (docker compose --profile prod ps) | Out-String
  Write-Host $psOut
  if ($psOut -notmatch "backend" -or $psOut -notmatch "rasa" -or $psOut -notmatch "nginx") {
    Write-Host "⚠️  Algunos servicios clave no figuran en 'ps'." -ForegroundColor Yellow
  }
} catch {
  Write-Host "✖ docker compose ps falló" -ForegroundColor Red
  $allOk = $false
}

# 2) Health checks
$hcBackend = Try-Command -Name "Backend /chat/health" -Cmd {
  Invoke-WebRequest -Uri "http://localhost:8000/chat/health" -UseBasicParsing -TimeoutSec 10 | Out-Null
}

$hcRasa = Try-Command -Name "Rasa /status" -Cmd {
  Invoke-WebRequest -Uri "http://localhost:5005/status" -UseBasicParsing -TimeoutSec 10 | Out-Null
}

$hcNginx = Try-Command -Name "Nginx / (200)" -Cmd {
  $resp = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
  if ($resp.StatusCode -ne 200) { throw "Nginx no devolvió 200" }
  $resp
}

$allOk = $allOk -and $hcBackend.ok -and $hcRasa.ok -and $hcNginx.ok

# 3) Round-trip bot vía Nginx → /rasa/webhooks/rest/webhook
$botOk = $false
if ($hcRasa.ok -and $hcNginx.ok) {
  try {
    $json = '{"sender":"smoke","message":"hola"}'
    $resp = Invoke-RestMethod -Method Post -Uri "http://localhost/rasa/webhooks/rest/webhook" -ContentType "application/json" -Body $json -TimeoutSec 10
    if ($resp -and $resp.Count -ge 1) {
      Write-Host "✔ Bot round-trip OK" -ForegroundColor Green
      $botOk = $true
    } else {
      Write-Host "✖ Bot round-trip vacío" -ForegroundColor Red
    }
  } catch {
    Write-Host "✖ Bot round-trip falló: $($_.Exception.Message)" -ForegroundColor Red
  }
} else {
  Write-Host "⏭️  Omitido round-trip bot: Rasa/Nginx no OK" -ForegroundColor Yellow
}

$allOk = $allOk -and $botOk

# 4) Admin SPA 200 (ya verificado en Nginx). Reafirmamos encabezados básicos.
if ($hcNginx.ok) {
  try {
    $head = Invoke-WebRequest -Method Head -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
    if ($head.StatusCode -eq 200) {
      Write-Host "✔ Admin SPA HEAD 200" -ForegroundColor Green
    } else {
      Write-Host "⚠️ Admin SPA HEAD != 200 ($($head.StatusCode))" -ForegroundColor Yellow
      $allOk = $false
    }
  } catch {
    Write-Host "✖ Admin SPA HEAD falló" -ForegroundColor Red
    $allOk = $false
  }
}

# Abrir navegador si se pidió
if ($Open -and $allOk) {
  Start-Process "http://localhost"
  Start-Process "http://localhost:8000/docs"
}

# Logs si algo falló y se pidió
if ($Logs -and -not $allOk) {
  Write-Host "`n>> Logs (Ctrl+C para salir)" -ForegroundColor Cyan
  docker compose --profile prod logs -f backend rasa nginx
}

if ($allOk) {
  Write-Host "`n✅ SMOKE PROD OK — todo listo para la sustentación." -ForegroundColor Green
  exit 0
} else {
  Write-Host "`n❌ SMOKE PROD FALLÓ — revisa los logs indicados." -ForegroundColor Red
  exit 1
}