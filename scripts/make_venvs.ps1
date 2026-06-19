Param(
  [switch]$Backend311,   # crea backend\.venv con Python 3.11
  [switch]$Backend312,   # crea backend\.venv con Python 3.12 (default)
  [switch]$Rasa311       # crea rasa\.venv con Python 3.11
)

$ErrorActionPreference = "Stop"

function Make-Venv {
  param(
    [string]$Path,
    [string]$PyLauncher,   # ej: py -3.11 o py -3.12
    [string]$ReqsFile      # ej: requirements.txt (opcional)
  )
  if (!(Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
  Push-Location $Path
  try {
    Write-Host "→ Creando venv en $(Get-Location) con $PyLauncher" -ForegroundColor Cyan
    & $PyLauncher -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    python -m pip install -U pip wheel
    if (Test-Path $ReqsFile) {
      Write-Host "→ Instalando dependencias de $ReqsFile" -ForegroundColor Cyan
      pip install -r $ReqsFile
    }
    Write-Host "✔ venv creado en $Path\.venv" -ForegroundColor Green
  } finally {
    Pop-Location
  }
}

# Defaults
if (-not $Backend311 -and -not $Backend312 -and -not $Rasa311) {
  $Backend312 = $true
}

# Backend 3.12 (recomendado)
if ($Backend312) {
  Make-Venv -Path "backend" -PyLauncher "py -3.12" -ReqsFile "requirements.txt"
  Write-Host "Comando para arrancar backend local:" -ForegroundColor Yellow
  Write-Host "  cd backend; .\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
}

# Backend 3.11 (opcional)
if ($Backend311) {
  Make-Venv -Path "backend" -PyLauncher "py -3.11" -ReqsFile "requirements.txt"
}

# Rasa/Actions 3.11 (solo si NO usas Docker para ellos)
if ($Rasa311) {
  if (!(Test-Path "rasa")) { Write-Host "⚠ No existe carpeta 'rasa' en la raíz." -ForegroundColor Yellow }
  else {
    Make-Venv -Path "rasa" -PyLauncher "py -3.11" -ReqsFile ""
    Push-Location "rasa"
    try {
      & .\.venv\Scripts\Activate.ps1
      Write-Host "→ Instalando Rasa/Rasa-SDK 3.6.x" -ForegroundColor Cyan
      pip install rasa==3.6.* rasa-sdk==3.6.*
      Write-Host "Comandos recomendados:" -ForegroundColor Yellow
      Write-Host "  # Terminal 1: rasa run --enable-api --cors '*' --port 5005" -ForegroundColor Yellow
      Write-Host "  # Terminal 2: python -m rasa_sdk --actions actions --port 5055" -ForegroundColor Yellow
    } finally {
      Pop-Location
    }
  }
}

Write-Host "Listo. (usa -h para ver flags)" -ForegroundColor Green