<#  run-prod.ps1
    Arranca el entorno PROD (perfil "prod") de Chatbot Tutor Virtual.
    Uso:
      .\run-prod.ps1                # build/arranque normal
      .\run-prod.ps1 -NoCache       # build sin caché
      .\run-prod.ps1 -Logs          # sigue logs clave
      .\run-prod.ps1 -Open          # abre navegador a /
#>

param(
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

# Perfiles y BuildKit SOLO para esta sesión
$env:COMPOSE_PROFILES = "prod"
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Servicios que se construyen en prod
# (ajusta si tu compose tiene targets específicos)
$servicesToBuild = @("backend","rasa","action-server","admin","nginx")

# Build: sin args especiales (prod usa imágenes/targets prod)
$buildCmd = @("compose","--profile","prod","build")
if ($NoCache) { $buildCmd += "--no-cache" }
$buildCmd += $servicesToBuild

Write-Host ">> docker $($buildCmd -join ' ')" -ForegroundColor Yellow
docker $buildCmd

# Levantar todo prod
$upCmd = @("compose","--profile","prod","up","-d")
Write-Host ">> docker $($upCmd -join ' ')" -ForegroundColor Yellow
docker $upCmd

# Health-check helper
function Test-Endpoint {
  param(
    [string]$Url,
    [string]$Name,
    [int]$Retries = 20,
    [int]$DelaySec = 3
  )
  for ($i=1; $i -le $Retries; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        Write-Host "✔ $Name OK ($($resp.StatusCode)) → $Url" -ForegroundColor Green
        return $true
      }
    } catch { }
    Write-Host "… esperando $Name ($i/$Retries)" -ForegroundColor DarkYellow
    Start-Sleep -Seconds $DelaySec
  }
  Write-Host "✖ $Name NO responde → $Url" -ForegroundColor Red
  return $false
}

# Chequeos básicos prod
$okBackend = Test-Endpoint -Url "http://localhost:8000/chat/health" -Name "Backend"
$okRasa    = Test-Endpoint -Url "http://localhost:5005/status"     -Name "Rasa"
$okNginx   = Test-Endpoint -Url "http://localhost"                  -Name "Nginx (admin)"

# Abrir navegador si todo va bien (o igual, para verificar)
if ($Open) {
  Start-Process "http://localhost"            # Nginx sirviendo SPA admin y rutas proxy
  Start-Process "http://localhost:8000/docs"  # Swagger del backend
}

# Logs en vivo (Ctrl+C para salir)
if ($Logs) {
  Write-Host ">> Logs (Ctrl+C para salir)" -ForegroundColor Cyan
  docker compose --profile prod logs -f backend rasa nginx admin
}

if ($okBackend -and $okRasa -and $okNginx) {
  Write-Host "`n✅ Entorno PROD listo. Backend, Rasa y Nginx responden." -ForegroundColor Green
} else {
  Write-Host "`n⚠️ PROD levantado, pero algún health-check falló. Revisa logs." -ForegroundColor Yellow
}
