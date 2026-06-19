Param(
    [ValidateSet('shell','train-run','train-shell')]
    [string]$Mode = 'shell',

    [switch]$Docker,
    [string]$ContainerName = 'ctv_rasa'
)

function Run-Rasa([string]$args) {
    if ($Docker) {
        Write-Host "🐳 docker exec -it $ContainerName rasa $args" -ForegroundColor Cyan
        docker exec -it $ContainerName rasa $args
    } else {
        Write-Host "💻 rasa $args" -ForegroundColor Cyan
        rasa $args
    }
}

switch ($Mode) {
    'shell' {
        Write-Host "=== Rasa shell ===" -ForegroundColor Cyan
        Run-Rasa 'shell'
    }
    'train-run' {
        Write-Host "🚀 Entrenando modelo Rasa..." -ForegroundColor Yellow
        Run-Rasa 'train'
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Error en el entrenamiento. Revisa NLU/rules/stories." -ForegroundColor Red
            exit 1
        }
        Write-Host "🌐 Levantando servidor Rasa en http://localhost:5005 ..." -ForegroundColor Yellow
        Run-Rasa 'run --enable-api --cors "*"'
    }
    'train-shell' {
        Write-Host "🚀 Entrenando modelo Rasa..." -ForegroundColor Yellow
        Run-Rasa 'train'
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Error en el entrenamiento. Revisa NLU/rules/stories." -ForegroundColor Red
            exit 1
        }
        Write-Host "💬 Abriendo Rasa shell para pruebas..." -ForegroundColor Yellow
        Run-Rasa 'shell'
    }
}
