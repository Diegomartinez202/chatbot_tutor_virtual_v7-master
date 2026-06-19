# scripts\run-smoke.ps1
[CmdletBinding()]
param(
  [string]$ComposeFile = "docker-compose.tester.yml",
  [string]$ProxyBase   = "http://nginx-dev",
  [string]$Backend     = "http://backend-dev:8000",
  [string]$Rasa        = "http://rasa:5005",
  [string]$PytestPath  = "test",
  [string]$ReportHtml  = "reports/smoke.html"
)

$ErrorActionPreference = "Stop"
Write-Host "🧪 Ejecutando smoke tests con $ComposeFile" -ForegroundColor Cyan

# Red externa
$net = docker network ls --format "{{.Name}}" | Select-String -SimpleMatch "tutorbot-local_app-net"
if (-not $net) {
  throw "❌ No existe la red externa 'tutorbot-local_app-net'. Levanta el stack: docker compose -p tutorbot-local up -d"
}

# Exporta variables al `run`
$env:PROXY_BASE        = $ProxyBase
$env:BACKEND           = $Backend
$env:RASA              = $Rasa
$env:PYTEST_PATH       = $PytestPath
$env:PYTEST_HTML       = $ReportHtml
$env:PYTHONUTF8        = "1"
$env:PYTHONIOENCODING  = "utf-8"
$env:PYTHONPATH        = "/app"

# 🔴 Clave para Pydantic: JSON válido como string
$env:ALLOWED_ORIGINS        = '["*"]'
$env:CORS_ALLOWED_ORIGINS   = '["*"]'  # por si tu Settings usa este nombre

docker compose -f $ComposeFile run --rm tester

# Abre reporte
$reportPath = Join-Path -Path (Get-Location) -ChildPath $ReportHtml
if (Test-Path $reportPath) {
  Write-Host "📄 Abriendo reporte: $reportPath" -ForegroundColor Green
  Start-Process $reportPath
} else {
  Write-Host "⚠️ No se encontró el reporte en: $reportPath" -ForegroundColor Yellow
}


