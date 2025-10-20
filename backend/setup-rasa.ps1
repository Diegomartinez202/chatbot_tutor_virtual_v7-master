Write-Host "🚀 Configurando entorno virtual con Python 3.10 para Rasa..." -ForegroundColor Cyan

# Detecta si Python 3.10 está instalado
$pythonPath = (Get-Command "python3.10" -ErrorAction SilentlyContinue)
if (-not $pythonPath) {
    Write-Host "⚠️ Python 3.10 no está instalado. Instalándolo con winget..." -ForegroundColor Yellow
    winget install Python.Python.3.10 -h
    Write-Host "✅ Python 3.10 instalado. Reinicia PowerShell y ejecuta de nuevo este script." -ForegroundColor Green
    exit
}

# Crear entorno si no existe
if (-not (Test-Path ".venv310")) {
    Write-Host "🧱 Creando entorno virtual (.venv310)..." -ForegroundColor Cyan
    py -3.10 -m venv .venv310
}

# Activar entorno
Write-Host "🟢 Activando entorno..."
.\.venv310\Scripts\Activate.ps1

# Actualizar pip
Write-Host "📦 Actualizando pip..."
python -m pip install --upgrade pip

# Instalar dependencias principales
Write-Host "⚙️ Instalando FastAPI, Uvicorn, Pydantic y Rasa (esto puede tardar)..."
pip install fastapi uvicorn pydantic rasa==3.6.20

# Generar requirements.txt
Write-Host "🧾 Guardando dependencias..."
pip freeze > requirements.txt

Write-Host "✅ Entorno completado. Ahora puedes abrir Visual Studio 2022 y usar .venv310 como intérprete." -ForegroundColor Green
pause