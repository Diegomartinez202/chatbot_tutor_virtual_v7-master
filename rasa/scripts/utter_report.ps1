# === CONFIGURACIÓN ===
# Ruta a la carpeta "rasa" de tu proyecto
$projectRoot = "C:\Users\USUARIO\Desktop\Proyectos\chatbot_tutor_virtual_v7-master\rasa"
$domainPath  = Join-Path $projectRoot "domain.yml"
$reportPath  = Join-Path $projectRoot "utterance_usage_report.csv"

Write-Host "Analizando utterances en:" $domainPath

# === 1. Extraer nombres de utterances desde domain.yml ===
$utterNames = @()

Get-Content $domainPath | ForEach-Object {
    if ($_ -match '^\s*(utter_[^:]+):') {
        $utterNames += $Matches[1]
    }
}

$utterNames = $utterNames | Sort-Object -Unique

Write-Host "Encontradas" $utterNames.Count "utterances en domain.yml"
Write-Host ""

# === 2. Analizar uso de cada utterance en todo el proyecto ===
$result = foreach ($utter in $utterNames) {

    $pattern = [regex]::Escape($utter)

    # Buscar en todos los .yml y .py dentro de la carpeta rasa
    $hits = Get-ChildItem -Path $projectRoot -Recurse -Include *.yml,*.py |
            Select-String -Pattern $pattern -ErrorAction SilentlyContinue

    $usedInDomain       = $hits | Where-Object { $_.Path -like "*domain.yml" }
    $usedOutsideDomain  = $hits | Where-Object { $_.Path -notlike "*domain.yml" }

    # Aparece en stories/rules (carpeta data/)
    $usedInStoriesRules = $usedOutsideDomain | Where-Object { $_.Path -like "*data*" } | Select-Object -First 1

    # Aparece en acciones (carpeta actions/)
    $usedInActions      = $usedOutsideDomain | Where-Object { $_.Path -like "*actions*" } | Select-Object -First 1

    # Clasificación
    $status = if ($usedInActions -or $usedInStoriesRules) { "PROTEGIDA" } else { "HUERFANA" }

    [PSCustomObject]@{
        Utterance        = $utter
        InDomain         = [bool]$usedInDomain
        InStoriesOrRules = [bool]$usedInStoriesRules
        InActions        = [bool]$usedInActions
        Status           = $status
    }
}

# === 3. Mostrar resumen por consola ===
$result |
    Sort-Object Status, Utterance |
    Format-Table -AutoSize

# === 4. Exportar a CSV para informes ===
$result |
    Sort-Object Status, Utterance |
    Export-Csv -Path $reportPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "Reporte generado en:" $reportPath
