<# 
  Uso:
    - Ejecutar normal (puerto 8000, con reload):
        powershell -ExecutionPolicy Bypass -File .\run_backend.ps1

    - Instalar dependencias antes de arrancar:
        powershell -ExecutionPolicy Bypass -File .\run_backend.ps1 -InstallDeps

    - Cambiar puerto:
        powershell -ExecutionPolicy Bypass -File .\run_backend.ps1 -Port 8010

    - Sin auto-reload:
        powershell -ExecutionPolicy Bypass -File .\run_backend.ps1 -NoReload
#>

param(
  [switch]$InstallDeps = $false,
  [int]$Port = 8000,
  [switch]$NoReload = $false
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Ok($msg)   { Write-Host "[OK]  $msg"  -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "[ERR] $msg"  -ForegroundColor Red }

# Detectar raíz del proyecto
$ProjectRoot = Split-Path -Parent $PSCommandPath
Set-Location $ProjectRoot
Write-Info "Proyecto: $ProjectRoot"

# 1️⃣ Activar entorno virtual
$VenvActivate = Join-Path $ProjectRoot 'backend\.venv310\Scripts\Activate.ps1'
if (!(Test-Path $VenvActivate)) {
  Write-Err "❌ No se encontró el entorno en $VenvActivate"
  Write-Err "Crea el entorno en backend:  py -3.10 -m venv .\backend\.venv310"
  exit 1
}
Write-Info "Activando entorno virtual..."
& $VenvActivate

# 2️⃣ Actualizar pip
try {
  Write-Info "Actualizando pip..."
  python -m pip install -U pip | Out-Null
  Write-Ok "pip actualizado correctamente."
} catch {
  Write-Warn "No se pudo actualizar pip: $($_.Exception.Message)"
}

# 3️⃣ Instalar dependencias si se solicita
if ($InstallDeps) {
  $Req = Join-Path $ProjectRoot 'backend\requirements.txt'
  if (Test-Path $Req) {
    Write-Info "Instalando dependencias desde $Req ..."
    python -m pip install -r $Req
    Write-Ok "Dependencias instaladas correctamente."
  } else {
    Write-Warn "No existe backend\requirements.txt — se omite instalación."
  }
}

# 4️⃣ Reiniciar Pylance (si está disponible)
function Restart-Pylance {
  try {
    & code --version | Out-Null
    & code --command "python.analysis.restartLanguageServer"
    Write-Ok "Pylance reiniciado con 'code'."
    return
  } catch {
    $CodeCmd = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
    if (Test-Path $CodeCmd) {
      & $CodeCmd --command "python.analysis.restartLanguageServer"
      Write-Ok "Pylance reiniciado con code.cmd."
      return
    } else {
      Write-Warn "No se encontró el comando 'code' en PATH."
      Write-Warn "Reinicia Pylance manualmente: Ctrl+Shift+P -> 'Pylance: Restart Language Server'."
    }
  }
}

Write-Info "Intentando reiniciar Pylance..."
Restart-Pylance

# 5️⃣ Configurar PYTHONPATH para backend y app
$paths = @(
  $ProjectRoot,
  (Join-Path $ProjectRoot 'backend'),
  (Join-Path $ProjectRoot 'app')
)
$env:PYTHONPATH = ($paths -join ';')

# 6️⃣ Arrancar el servidor Uvicorn
$ReloadFlag = ""
if (-not $NoReload) { $ReloadFlag = "--reload" }

Write-Info "Levantando backend en http://127.0.0.1:$Port ..."
Start-Process "cmd" -ArgumentList "/c start http://127.0.0.1:$Port/health" | Out-Null

# Ejecutar servidor
python -m uvicorn backend.main:app --host 0.0.0.0 --port $Port $ReloadFlag