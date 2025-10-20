param(
  [ValidateSet('build','prod')]
  [string]$Profile = 'build',
  [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

function Invoke-Compose {
  param([string[]]$Args)
  Write-Host "› docker compose $($Args -join ' ')" -ForegroundColor Cyan
  docker compose @Args
}

function Start-Stack {
  param([string]$Profile, [switch]$Rebuild)
  $args = @('--profile', $Profile, 'up', '-d')
  if ($Rebuild) { $args += '--build' }
  Invoke-Compose -Args $args
}

function Stop-Stack {
  param([string]$Profile)
  Invoke-Compose -Args @('--profile', $Profile, 'down')
}

function Logs {
  param([string]$Profile, [string]$Service = '')
  $args = @('--profile', $Profile, 'logs', '-f')
  if ($Service) { $args += $Service }
  Invoke-Compose -Args $args
}

function Test-Url {
  param([string]$Url, [string]$Name)
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $res = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 -Uri $Url
    $sw.Stop()
    if ($res.StatusCode -eq 200) {
      Write-Host ("[OK]  {0}  {1}ms" -f $Name, $sw.ElapsedMilliseconds) -ForegroundColor Green
      return $true
    }
  } catch {}
  $sw.Stop()
  Write-Host ("[FAIL] {0}" -f $Name) -ForegroundColor Red
  return $false
}

function Health {
  param([string]$Profile)
  Write-Host "=== Health ($Profile) ===" -ForegroundColor Yellow
  $ok1 = Test-Url "http://127.0.0.1:8000/chat/health" "FastAPI /chat/health"
  $ok2 = Test-Url "http://127.0.0.1:5005/status"       "Rasa /status"
  $ok3 = Test-Url "http://127.0.0.1:5055/health"       "Action-Server /health"
  if ($Profile -eq 'prod') {
    $ok4 = Test-Url "http://127.0.0.1/"                 "Nginx / (Admin)"
    $ok5 = Test-Url "http://127.0.0.1/api/chat/health"  "Nginx → /api"
    $ok6 = Test-Url "http://127.0.0.1/rasa/status"      "Nginx → /rasa"
  }
}

function Start-BackendLocal {
  # Arranca el backend con tu venv (sin Docker) para debugging local
  param(
    [string]$VenvPath = ".\backend\.venv",
    [int]$Port = 8000
  )
  $py = Join-Path $VenvPath "Scripts\python.exe"
  if (-not (Test-Path $py)) {
    Write-Error "No encontré $py. Crea el venv en backend\.venv primero."
  }
  Push-Location ".\backend"
  & $py -m uvicorn backend.main:app --host 0.0.0.0 --port $Port --reload
  Pop-Location
}

# Auto-run si llamas:  .\scripts\tasks.ps1 -Profile build -Rebuild
Start-Stack -Profile $Profile -Rebuild:$Rebuild
Health -Profile $Profile
Write-Host "👉 Logs (Ctrl+C para salir):" -ForegroundColor Cyan
Logs -Profile $Profile