Param(
    [switch]$OnlyAdapted  # si lo usas, corre solo backend/test_adapted
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "=== 🧪 Ejecutando pruebas del Chatbot Tutor Virtual ===" -ForegroundColor Cyan

# 1) Crear carpeta de reportes
$reportsDir = Join-Path $here "reports"
if (!(Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir | Out-Null
}

# 2) Activar entorno virtual si existe
$venv = Join-Path $here ".venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    Write-Host ">> Activando entorno virtual .venv..." -ForegroundColor DarkCyan
    & $venv
} else {
    Write-Host "⚠ No se encontró .venv\. Usa tu entorno manualmente o crea uno con:  python -m venv .venv" -ForegroundColor Yellow
}

# 3) Asegurar dependencias mínimas de test
Write-Host ">> Instalando dependencias de pruebas (pytest, pytest-html, coverage)..." -ForegroundColor DarkCyan
python -m pip install -U pip
python -m pip install pytest pytest-html coverage

# 4) Construir comando base de pytest
if ($OnlyAdapted) {
    $testPath = "backend/test_adapted"
} else {
    # puedes cambiar esto si quieres que incluya TODO backend/test
    $testPath = "backend/test_adapted"
}

$pytestHtml = Join-Path $reportsDir "pytest-report.html"
$pytestCmd = @(
    "-m", "pytest",
    $testPath,
    "--maxfail=1",
    "--disable-warnings",
    "--tb=short",
    "--html=$pytestHtml",
    "--self-contained-html"
)

Write-Host ">> Ejecutando pytest con reporte HTML..." -ForegroundColor DarkCyan
Write-Host "python $($pytestCmd -join ' ')" -ForegroundColor DarkGray

python $pytestCmd
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Algunas pruebas fallaron. Revisa el reporte: $pytestHtml" -ForegroundColor Red
} else {
    Write-Host "✅ Pytest finalizado sin errores." -ForegroundColor Green
}

# 5) coverage.py sobre los tests adaptados
$covFile = Join-Path $reportsDir ".coverage"
$covHtmlDir = Join-Path $reportsDir "htmlcov_adapted"

Write-Host ">> Ejecutando coverage sobre $testPath ..." -ForegroundColor DarkCyan
# coverage run -m pytest backend/test_adapted
coverage run --source=backend -m pytest $testPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Coverage detectó fallos en las pruebas. Revisa la salida de pytest." -ForegroundColor Yellow
} else {
    Write-Host "✅ Coverage ejecutado correctamente." -ForegroundColor Green
}

Write-Host ">> Generando reporte HTML de coverage..." -ForegroundColor DarkCyan
coverage html -d $covHtmlDir

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Reportes generados:" -ForegroundColor Cyan
Write-Host "  - Pytest HTML : $pytestHtml" -ForegroundColor Green
Write-Host "  - Coverage    : $covHtmlDir\index.html" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sugerencia: abre estos archivos en el navegador y toma capturas para el informe." -ForegroundColor DarkGray
