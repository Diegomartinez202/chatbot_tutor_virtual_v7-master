param (
    [string]$mode
)

$nginxConfDir = "ops/nginx/conf.d"

Write-Host "=== Reset Nginx Configuration ==="

if (-not (Test-Path $nginxConfDir)) {
    Write-Host "❌ No existe la carpeta $nginxConfDir"
    exit 1
}

function Switch-Config($target) {
    $src = Join-Path $nginxConfDir "$target.conf"
    $dest = Join-Path $nginxConfDir "default.conf"

    if (-not (Test-Path $src)) {
        Write-Host "❌ No se encontró $src"
        exit 1
    }

    Copy-Item $src $dest -Force
    Write-Host "✅ Configuración cambiada a $target"
}

if (-not $mode) {
    Write-Host "Selecciona un modo:"
    Write-Host "1. dev.conf"
    Write-Host "2. prod.conf"
    Write-Host "3. prod-https.conf"
    $choice = Read-Host "Elige 1/2/3"

    switch ($choice) {
        1 { Switch-Config "dev" }
        2 { Switch-Config "prod" }
        3 { Switch-Config "prod-https" }
        default { Write-Host "❌ Opción inválida" }
    }
} else {
    Switch-Config $mode
}