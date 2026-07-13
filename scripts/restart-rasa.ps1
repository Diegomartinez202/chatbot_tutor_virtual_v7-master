param(
    [Parameter(Mandatory=$true)]
    [string]$Container
)

. "$PSScriptRoot\wait-rasa.ps1"

Write-Host ""
Write-Host "Reiniciando Rasa..." -ForegroundColor Cyan

docker restart $Container | Out-Null

if ($LASTEXITCODE -ne 0){

    Write-Host "No fue posible reiniciar Rasa." -ForegroundColor Red
    exit 1

}

if (-not (Wait-Rasa -Container $Container)) {

    Write-Host ""
    Write-Host "El reinicio de Rasa falló." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Rasa reiniciado correctamente." -ForegroundColor Green