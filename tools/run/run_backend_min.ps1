# run_backend_min.ps1  (colócalo en la raíz del repo)
$ErrorActionPreference = 'Stop'

# 1) Ir a la raíz del proyecto (donde está este script)
$projectRoot = Split-Path -Parent $PSCommandPath
Set-Location $projectRoot

# 2) Activar entorno virtual (backend\.venv310)
$venv = Join-Path $projectRoot 'backend\.venv310\Scripts\Activate.ps1'
if (!(Test-Path $venv)) {
  Write-Host 'No se encontró el entorno: backend\.venv310. Crea uno con:  py -3.10 -m venv .\backend\.venv310' -ForegroundColor Red
  exit 1
}
& $venv

# 3) Actualizar pip e instalar deps si existe requirements.txt
python -m pip install -U pip
$req = Join-Path $projectRoot 'backend\requirements.txt'
if (Test-Path $req) { python -m pip install -r $req }

# 4) Reiniciar Pylance (best-effort)
try {
  & code --command 'python.analysis.restartLanguageServer'
} catch {
  $codecmd = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"
  if (Test-Path $codecmd) { & $codecmd --command 'python.analysis.restartLanguageServer' }
}

# 5) Configurar PYTHONPATH para que backend y app se resuelvan
$env:PYTHONPATH = ($projectRoot + ';' + (Join-Path $projectRoot 'backend') + ';' + (Join-Path $projectRoot 'app'))

# 6) Abrir /health y levantar uvicorn
$port = 8000
Start-Process ("http://127.0.0.1:" + $port + "/health")
python -m uvicorn backend.main:app --host 0.0.0.0 --port $port --reload