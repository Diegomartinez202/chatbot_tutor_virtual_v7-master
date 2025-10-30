# switch-env.ps1 — alterna entre dev y prod sin sobrescribir tu .env
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev','prod')]
    [string]$Mode
)

$EnvFile  = ".env"
$RootDev  = ".env.root.dev"
$RootProd = ".env.root.prod"

Write-Host ("Cambiando entorno a: {0}" -f $Mode)

# Asegura que .env exista
if (-not (Test-Path $EnvFile)) {
    New-Item -ItemType File -Path $EnvFile | Out-Null
    Write-Host "Creado .env (vacío)"
}

# (Opcional) fusionar plantillas sin sobrescribir (si existen)
if ($Mode -eq 'dev' -and (Test-Path $RootDev)) {
    Write-Host "Fusionando .env.root.dev → .env (append no destructivo)"
    Get-Content $RootDev | Add-Content $EnvFile
}
elseif ($Mode -eq 'prod' -and (Test-Path $RootProd)) {
    Write-Host "Fusionando .env.root.prod → .env (append no destructivo)"
    Get-Content $RootProd | Add-Content $EnvFile
}

# Carga y filtra líneas antiguas de las 3 claves que gestionamos
$Lines    = Get-Content $EnvFile
$Filtered = $Lines | Where-Object { $_ -notmatch '^\s*(MODE|BACKEND_ENV_FILE|COMPOSE_PROFILES)\s*=' }

# Construye bloque según modo
$Block = @(
    '# ========================',
    '# MODE (auto-generated)',
    '# ========================'
)

if ($Mode -eq 'prod') {
    $Block += 'MODE=prod'
    $Block += 'BACKEND_ENV_FILE=backend/.env.production'
    $Block += 'COMPOSE_PROFILES=prod'
}
else {
    $Block += 'MODE=dev'
    $Block += 'BACKEND_ENV_FILE=backend/.env.dev'
    # Usa "build" si ese es tu perfil de compose para dev
    $Block += 'COMPOSE_PROFILES=build'
}

# Escribe nuevo .env (bloque + línea en blanco + resto filtrado)
$Final = @()
$Final += $Block
$Final += ''
$Final += $Filtered
Set-Content -Path $EnvFile -Value $Final -Encoding UTF8

$BE = ($Block | Where-Object { $_ -like 'BACKEND_ENV_FILE=*' }) -replace '.*='
$CP = ($Block | Where-Object { $_ -like 'COMPOSE_PROFILES=*' }) -replace '.*='

Write-Host ("OK .env actualizado. Modo: {0}" -f $Mode)
Write-Host ("  BACKEND_ENV_FILE={0}" -f $BE)
Write-Host ("  COMPOSE_PROFILES={0}" -f $CP)
