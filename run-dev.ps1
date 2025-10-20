<#  run-dev.ps1
    Arranca el entorno DEV (perfil "build") de Chatbot Tutor Virtual.
    Uso:
      .\run-dev.ps1                # build/arranque normal
      .\run-dev.ps1 -NoPoppler     # build sin poppler-utils
      .\run-dev.ps1 -NoCache       # build sin caché
      .\run-dev.ps1 -Logs          # sigue logs de backend y Rasa
      .\run-dev.ps1 -Open          # abre navegador a /, /docs, :5173
#>

param(
  [switch]$NoPoppler,
  [switch]$NoCache,
  [switch]$Logs,
  [switch]$Open
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Ir a la raíz del repo (donde está este script)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host ">> Carpeta del repo: $repoRoot" -ForegroundColor Cyan

# Perfiles y BuildKit
$env:COMPOSE_PROFILES = "build"
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Servicios que realmente requieren build
$servicesToBuild = @("backend-dev","rasa","action-server")  # admin-dev usa imagen node y npm ci en runtime

# Build args
$buildArgs = @()
if ($NoPoppler) { $buildArgs += @("--build-arg","WITH_POPPLER=false") }

# Comando de build
$buildCmd = @("compose","--profile","build","build")
if ($NoCache) { $buildCmd += "--no-cache" }
$buildCmd += $buildArgs
$buildCmd += $servicesToBuild

# Ejecutar build
Write-Host ">> docker $($buildCmd -join ' ')" -ForegroundColor Yellow
docker $buildCmd

# Levantar todo el perfil build
$upCmd = @("compose","--profile","build","up","-d")
Write-Host ">> docker $($upCmd -join ' ')" -ForegroundColor Yellow
docker $upCmd

# Función simple de health-check con reintentos
function Test-Endpoint {
  param(
    [string]$Url,
    [string]$Name,
    [int]$Retries = 10,
    [int]$DelaySec = 3
  )
  for ($i=1; $i -le $Retries; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        Write-Host "✔ $Name OK ($($resp.StatusCode)) → $Url" -ForegroundColor Green
        return $true
      }
    } catch {
      # silencio y reintento
    }
    Write-Host "… esperando $Name ($i/$Retries)" -ForegroundColor DarkYellow
    Start-Sleep -Seconds $DelaySec
  }
  Write-Host "✖ $Name NO responde → $Url" -ForegroundColor Red
  return $false
}

# Health checks básicos
$okBackend = Test-Endpoint -Url "http://localhost:8000/chat/health" -Name "Backend"
$okRasa    = Test-Endpoint -Url "http://localhost:5005/status"     -Name "Rasa"

# Abrir navegador
if ($Open) {
  Start-Process "http://localhost"
  Start-Process "http://localhost:8000/docs"
  Start-Process "http://localhost:5173"
}

# Logs en vivo
if ($Logs) {
  Write-Host ">> Logs (Ctrl+C para salir)" -ForegroundColor Cyan
  docker compose --profile build logs -f backend-dev rasa
}

if ($okBackend -and $okRasa) {
  Write-Host "`n✅ Entorno DEV listo. Backend y Rasa responden." -ForegroundColor Green
} else {
  Write-Host "`n⚠️ DEV levantado, pero algún health-check falló. Revisa logs." -ForegroundColor Yellow
}