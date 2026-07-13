param(
    [Parameter(Mandatory=$true)]
    [string]$Container
)

Write-Host ""
Write-Host "===============================" -ForegroundColor Cyan
Write-Host " VALIDANDO PROYECTO RASA "
Write-Host "===============================" -ForegroundColor Cyan

docker exec $Container sh -lc "cd /app/rasa && rasa data validate --max-history 5"

if ($LASTEXITCODE -ne 0){

    Write-Host ""
    Write-Host "La validación falló." -ForegroundColor Red

    exit 1

}

Write-Host ""
Write-Host "Validación correcta." -ForegroundColor Green
