<# 
prefix_backend_imports.ps1 (fix)
Añade el prefijo "backend." a imports de: routes, models, services, utils, schemas
• Limita el alcance a la carpeta "backend/" para evitar .venv/site-packages
• Dry-run por defecto; usa -Apply para escribir
#>

param([switch]$Apply)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($m){ Write-Host "==> $m" -ForegroundColor Cyan }

# 1) Limitar a backend/
$repoRoot = Get-Location
$root = Join-Path $repoRoot "backend"
if (-not (Test-Path $root)) { throw "No se encontró carpeta 'backend' en: $repoRoot" }

# 2) Recorrer sólo .py del proyecto (no .venv, no node_modules)
$files = Get-ChildItem -Path $root -Recurse -File -Filter "*.py" | Where-Object {
  $_.FullName -notmatch "(\\__pycache__\\|\\node_modules\\|\\dist\\|\\build\\|\\\.mypy_cache\\|\\\.ruff_cache\\|\\\.pytest_cache\\)"
}

# Reglas FROM ... IMPORT ...
$fromPatterns = @(
  '(?m)^(?<indent>[ \t]*from[ \t]+)(routes)(?=[ \t]+import\b)',
  '(?m)^(?<indent>[ \t]*from[ \t]+)(models)(?=[ \t]+import\b)',
  '(?m)^(?<indent>[ \t]*from[ \t]+)(services)(?=[ \t]+import\b)',
  '(?m)^(?<indent>[ \t]*from[ \t]+)(utils)(?=[ \t]+import\b)',
  '(?m)^(?<indent>[ \t]*from[ \t]+)(schemas)(?=[ \t]+import\b)'
)
$fromRepls = @(
  '${indent}backend.routes',
  '${indent}backend.models',
  '${indent}backend.services',
  '${indent}backend.utils',
  '${indent}backend.schemas'
)

# Reglas IMPORT ... (múltiples módulos separados por coma)
$importFirstToken = @(
  '(?m)^(?<indent>[ \t]*import[ \t]+)routes\b',
  '(?m)^(?<indent>[ \t]*import[ \t]+)models\b',
  '(?m)^(?<indent>[ \t]*import[ \t]+)services\b',
  '(?m)^(?<indent>[ \t]*import[ \t]+)utils\b',
  '(?m)^(?<indent>[ \t]*import[ \t]+)schemas\b'
)
$importFirstRepls = @(
  '${indent}backend.routes',
  '${indent}backend.models',
  '${indent}backend.services',
  '${indent}backend.utils',
  '${indent}backend.schemas'
)
$importNextTokens = @(
  '(?<=,|\s)routes\.',
  '(?<=,|\s)models\.',
  '(?<=,|\s)services\.',
  '(?<=,|\s)utils\.',
  '(?<=,|\s)schemas\.',
  '(?<=,|\s)routes\b(?!\.)',
  '(?<=,|\s)models\b(?!\.)',
  '(?<=,|\s)services\b(?!\.)',
  '(?<=,|\s)utils\b(?!\.)',
  '(?<=,|\s)schemas\b(?!\.)'
)
$importNextRepls = @(
  'backend.routes.',
  'backend.models.',
  'backend.services.',
  'backend.utils.',
  'backend.schemas.',
  'backend.routes',
  'backend.models',
  'backend.services',
  'backend.utils',
  'backend.schemas'
)

Write-Step "Escaneando 'backend/' y normalizando imports con prefijo 'backend.' (dry-run: $(-not $Apply))"
$changed = @()

foreach ($f in $files) {
  $content = $null
  try {
    $content = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
  } catch {
    try { $content = Get-Content -LiteralPath $f.FullName -Raw -Encoding Default } catch { $content = $null }
  }
  if ([string]::IsNullOrEmpty($content)) { continue }

  $orig = $content

  for ($i=0; $i -lt $fromPatterns.Count; $i++) {
    $rx = [regex]$fromPatterns[$i]
    $rp = $fromRepls[$i]
    $content = $rx.Replace($content, $rp)
  }
  for ($i=0; $i -lt $importFirstToken.Count; $i++) {
    $rx = [regex]$importFirstToken[$i]
    $rp = $importFirstRepls[$i]
    $content = $rx.Replace($content, $rp)
  }
  for ($i=0; $i -lt $importNextTokens.Count; $i++) {
    $rx = [regex]$importNextTokens[$i]
    $rp = $importNextRepls[$i]
    $content = $rx.Replace($content, $rp)
  }

  if ($content -ne $orig) {
    if ($Apply) {
      Copy-Item -LiteralPath $f.FullName -Destination ($f.FullName + ".bak") -Force
      Set-Content -LiteralPath $f.FullName -Value $content -Encoding UTF8
      Write-Host "✔ Actualizado: $($f.FullName)" -ForegroundColor Green
    } else {
      Write-Host "[dry-run] Cambiaría imports en: $($f.FullName)"
    }
    $changed += $f.FullName
  }
}

Write-Step ("Archivos con cambios: {0}" -f $changed.Count)
if ($changed.Count -gt 0) {
  $report = Join-Path $repoRoot "prefix_backend_report.txt"
  $changed | Set-Content -Path $report -Encoding UTF8
  Write-Host ("Reporte: {0}" -f $report) -ForegroundColor Cyan
}
Write-Host "Listo." -ForegroundColor Magenta