$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path "$PSScriptRoot\..").Path
$InteractiveDir = Join-Path $RootDir "interactive"

New-Item -ItemType Directory -Force -Path $InteractiveDir | Out-Null

Write-Host "🚀 Iniciando Rasa Interactive..."
Write-Host "👉 Al terminar, exporta a:"
Write-Host "   $InteractiveDir\nlu_interactive.yml"
Write-Host "   $InteractiveDir\stories_interactive.yml"
Write-Host "   $InteractiveDir\rules_interactive.yml"
Write-Host ""

Set-Location $RootDir
rasa interactive
