# switch-env.ps1 — alterna entre dev y prod de forma segura e inteligente
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev','prod')]
    [string]$Mode
)

$EnvFile  = ".env"
$RootDev  = ".env.root.dev"
$RootProd = ".env.root.prod"

Write-Host ("Cambiando entorno a: {0}" -f $Mode)

# Asegura que .env exista sin borrar su contenido
if (-not (Test-Path $EnvFile)) {
    New-Item -ItemType File -Path $EnvFile | Out-Null
    Write-Host "Creado .env (vacío)"
}

# Carga las líneas actuales del .env para comparar
$CurrentLines = Get-Content $EnvFile

# Función para fusionar de forma inteligente (Evita duplicados)
function Merge-EnvTemplate ($TemplatePath) {
    if (Test-Path $TemplatePath) {
        Write-Host "Revisando plantilla $TemplatePath para añadir variables faltantes..."
        $TemplateLines = Get-Content $TemplatePath
        foreach ($Line in $TemplateLines) {
            # Ignorar comentarios, líneas vacías y las variables autogeneradas
            if ($Line -match '^\s*#' -or $Line -match '^\s*$' -or $Line -match '^\s*(MODE|BACKEND_ENV_FILE|COMPOSE_PROFILES)\s*=') {
                continue
            }
            # Extraer el nombre de la variable (ej: JWT_ISSUER)
            if ($Line -match '^\s*([^=]+)=') {
                $VarName = $Matches[1].Trim()
                # Si la variable NO existe en el .env actual, la añade de forma segura
                if (-not ($CurrentLines -match "^\s*$VarName\s*=")) {
                    Add-Content -Path $EnvFile -Value $Line
                    Write-Host "  + Añadida variable faltante: $VarName"
                }
            }
        }
    }
}

# Ejecuta la fusión inteligente según el modo
if ($Mode -eq 'dev') {
    Merge-EnvTemplate $RootDev
}
elseif ($Mode -eq 'prod') {
    Merge-EnvTemplate $RootProd
}

# Carga y filtra líneas antiguas de las 3 claves autogeneradas
$Lines    = Get-Content $EnvFile
$Filtered = $Lines | Where-Object { $_ -notmatch '^\s*(MODE|BACKEND_ENV_FILE|COMPOSE_PROFILES)\s*=' }

# Construye bloque autogenerado según modo
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
    $Block += 'COMPOSE_PROFILES=build'
}

# Reescribe el .env limpiando la cabecera autogenerada pero manteniendo TODO lo demás intacto
$Final = @()
$Final += $Block
$Final += ''
$Final += $Filtered
Set-Content -Path $EnvFile -Value $Final -Encoding UTF8

$BE = ($Block | Where-Object { $_ -like 'BACKEND_ENV_FILE=*' }) -replace '.*='
$CP = ($Block | Where-Object { $_ -like 'COMPOSE_PROFILES=*' }) -replace '.*='

Write-Host ("OK .env actualizado sin pérdida de datos. Modo: {0}" -f $Mode)
Write-Host ("  BACKEND_ENV_FILE={0}" -f $BE)
Write-Host ("  COMPOSE_PROFILES={0}" -f $CP)
