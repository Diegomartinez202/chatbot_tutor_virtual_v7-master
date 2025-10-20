<#  smoke-build.ps1
    Smoke test express de BUILD/DEV (perfil "build").
    Verifica:
      1) docker compose ps
      2) Health checks: backend-dev, rasa
      3) Round-trip de bot vía Nginx-dev → /rasa/webhooks/rest/webhook
      4) Admin-dev responde (200 en :80 vía nginx-dev y :5173 directo)
#>

param(
  [switch]$Open,
  [switch]$Logs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host "== Smoke BUILD | carpeta: $repoRoot ==" -ForegroundColor Cyan

# Perfil para esta ejecución
$env:COMPOSE_PROFILES = "build"

function Try-Command {
  param(
    [scriptblock]$Cmd,
    [string]$Name,
    [int]$Retries = 12,
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
  $psOut = (docker compose --profile build ps) | Out-String
  Write-Host $psOut
  if ($psOut -notmatch "backend-dev" -or $psOut -notmatch "rasa" -or $psOut -notmatch "nginx-dev") {
    Write-Host "⚠️  Faltan servicios clave en 'ps'." -ForegroundColor Yellow
  }
} catch {
  Write-Host "✖ docker compose ps falló" -ForegroundColor Red
  $allOk = $false
}

# 2) Health checks
$hcBackend = Try-Command -Name "Backend-dev /chat/health" -Cmd {
  Invoke-WebRequest -Uri "http://localhost:8000/chat/health" -UseBasicParsing -TimeoutSec 10 | Out-Null
}

$hcRasa = Try-Command -Name "Rasa /status" -Cmd {
  Invoke-WebRequest -Uri "http://localhost:5005/status" -UseBasicParsing -TimeoutSec 10 | Out-Null
}

# 3) Round-trip bot vía Nginx-dev → /rasa/webhooks/rest/webhook
$botOk = $false
if ($hcRasa.ok) {
  try {
    $json = '{"sender":"smoke","message":"hola"}'
    $resp = Invoke-RestMethod -Method Post -Uri "http://localhost/rasa/webhooks/rest/webhook" -ContentType "application/json" -Body $json -TimeoutSec 10
    if ($resp -and $resp.Count -ge 1) {
      Write-Host "✔ Bot round-trip (nginx-dev → rasa) OK" -ForegroundColor Green
      $botOk = $true
    } else {
      Write-Host "✖ Bot round-trip vacío" -ForegroundColor Red
    }
  } catch {
    Write-Host "✖ Bot round-trip falló: $($_.Exception.Message)" -ForegroundColor Red
  }
} else {
  Write-Host "⏭️  Omitido round-trip: Rasa no OK" -ForegroundColor Yellow
}

$allOk = $allOk -and $hcBackend.ok -and $hcRasa.ok -and $botOk

# 4) Admin SPA (vía nginx-dev y directo a Vite :5173)
$okNginx = Try-Command -Name "Nginx-dev / (200)" -Cmd {
  $resp = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 10
  if ($resp.StatusCode -ne 200) { throw "Nginx-dev no devolvió 200" }
  $resp | Out-Null
}
$okVite = Try-Command -Name "admin-dev :5173 (200)" -Cmd {
  $resp = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 10
  if ($resp.StatusCode -ne 200) { throw "admin-dev no devolvió 200" }
  $resp | Out-Null
}

$allOk = $allOk -and $okNginx.ok -and $okVite.ok

# Abrir navegador si pasa
if ($Open -and $allOk) {
  Start-Process "http://localhost"
  Start-Process "http://localhost:8000/docs"
  Start-Process "http://localhost:5173"
}

# Logs si se pidió y hay fallas
if ($Logs -and -not $allOk) {
  Write-Host "`n>> Logs (Ctrl+C para salir)" -ForegroundColor Cyan
  docker compose --profile build logs -f backend-dev rasa nginx-dev admin-dev
}

if ($allOk) {
  Write-Host "`n✅ SMOKE BUILD OK — dev listo." -ForegroundColor Green
  exit 0
} else {
  Write-Host "`n❌ SMOKE BUILD FALLÓ — revisa logs." -ForegroundColor Red
  exit 1
}