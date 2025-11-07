$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path "$PSScriptRoot\..").Path
$InteractiveDir = Join-Path $RootDir "interactive"
$DataDir = Join-Path $RootDir "data"

$DateTag = Get-Date -Format "yyyyMMdd_HHmmss"

$nluSrc     = Join-Path $InteractiveDir "nlu_interactive.yml"
$storiesSrc = Join-Path $InteractiveDir "stories_interactive.yml"
$rulesSrc   = Join-Path $InteractiveDir "rules_interactive.yml"

$nluDst     = Join-Path $DataDir "nlu\nlu_interactive_$DateTag.yml"
$storiesDst = Join-Path $DataDir "stories\stories_interactive_$DateTag.yml"
$rulesDst   = Join-Path $DataDir "rules\rules_interactive_$DateTag.yml"

New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "nlu") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "stories") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "rules") | Out-Null

$movedAny = $false

function Copy-IfPresent($src, $dst) {
    if ((Test-Path $src) -and ((Get-Item $src).Length -gt 0)) {
        if (-not (Test-Path $dst)) {
            Copy-Item -Path $src -Destination $dst
            Write-Host "➡️  Copiado: $src -> $dst"
            return $true
        } else {
            Write-Host "ℹ️  Ya existe destino (no se sobrescribe): $dst"
        }
    } else {
        Write-Host "⚠️  No existe o vacío: $src (omitido)"
    }
    return $false
}

$movedAny = (Copy-IfPresent $nluSrc $nluDst) -or $movedAny
$movedAny = (Copy-IfPresent $storiesSrc $storiesDst) -or $movedAny
$movedAny = (Copy-IfPresent $rulesSrc $rulesDst) -or $movedAny

if ($movedAny) {
    Set-Location $RootDir
    Write-Host "🔎 Validando datos..."
    rasa data validate

    Write-Host "🧠 Entrenando modelo..."
    rasa train

    Write-Host "✅ Listo. Modelos en: $RootDir\models"
} else {
    Write-Host "ℹ️ No había archivos interactivos con contenido."
}
