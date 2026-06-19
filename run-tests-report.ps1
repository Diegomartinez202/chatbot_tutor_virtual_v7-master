Param(
    [switch]$OnlyAdapted  # si lo usas, corre solo backend/test/test_adapted
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
$pytestHtml = Join-Path $reportsDir "pytest-report.html"

# Si $OnlyAdapted: apuntamos solo a backend/test/test_adapted
# Si NO: dejamos que pytest use pytest.ini y descubra TODO (sin ruta explícita)
if ($OnlyAdapted) {
    $pytestArgs = @(
        "-m", "pytest",
        "backend/test/test_adapted",
        "--maxfail=1",
        "--disable-warnings",
        "--tb=short",
        "--html=$pytestHtml",
        "--self-contained-html"
    )
} else {
    $pytestArgs = @(
        "-m", "pytest",
        "--maxfail=1",
        "--disable-warnings",
        "--tb=short",
        "--html=$pytestHtml",
        "--self-contained-html"
    )
}

Write-Host ">> Ejecutando pytest con reporte HTML..." -ForegroundColor DarkCyan
Write-Host "python $($pytestArgs -join ' ')" -ForegroundColor DarkGray

python $pytestArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Algunas pruebas fallaron. Revisa el reporte: $pytestHtml" -ForegroundColor Red
} else {
    Write-Host "✅ Pytest finalizado sin errores." -ForegroundColor Green
}

# 5) coverage.py
$covHtmlDir = Join-Path $reportsDir "htmlcov_adapted"

Write-Host ">> Ejecutando coverage..." -ForegroundColor DarkCyan

if ($OnlyAdapted) {
    # Solo sobre los tests adaptados
    coverage run --source=backend -m pytest backend/test/test_adapted
} else {
    # Sobre toda la suite que descubra pytest.ini
    coverage run --source=backend -m pytest
}

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
