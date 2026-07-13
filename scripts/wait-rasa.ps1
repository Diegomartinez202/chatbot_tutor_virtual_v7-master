function Wait-Rasa {

    param(
        [Parameter(Mandatory=$true)]
        [string]$Container,

        [int]$MaxAttempts = 60,

        [int]$DelaySeconds = 2
    )

    Write-Host ""
    Write-Host "Esperando que Rasa esté disponible..." -ForegroundColor Cyan

    for ($i = 1; $i -le $MaxAttempts; $i++) {

        Write-Host "Intento $i/$MaxAttempts..."

        docker exec $Container sh -lc "curl -fs http://localhost:5005/status >/dev/null" 2>$null

        if ($LASTEXITCODE -eq 0) {

            Write-Host ""
            Write-Host "Rasa disponible." -ForegroundColor Green

            return $true
        }

        Start-Sleep -Seconds $DelaySeconds
    }

    Write-Host ""
    Write-Host "ERROR: Rasa no respondió." -ForegroundColor Red

    return $false
}