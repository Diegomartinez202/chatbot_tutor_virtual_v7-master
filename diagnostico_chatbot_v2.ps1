# diagnostico_chatbot_v2.ps1
# Script de diagnóstico Docker Compose (perfil: prod)
# - Genera un log completo
# - Busca patrones de error críticos y muestra resumen
# Evita caracteres especiales para prevenir errores de parseo en PowerShell.

param(
    [int]$TailLines = 500,           # cuantas líneas tomar de logs por servicio
    [string]$Profile = "prod",       # perfil docker compose
    [switch]$FollowLive              # si se pasa, abre logs -f al final (manual)
)

# Preparación
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = ".\diagnostic_$timestamp.log"

function Write-Log {
    param([string]$text)
    $text | Tee-Object -FilePath $logFile -Append | Out-Default
}

function Run-Cmd {
    param([string]$cmd)
    Write-Host ">>> Ejecutando: $cmd" -ForegroundColor Cyan
    # Ejecuta el comando, redirige stderr a stdout y lo guarda en el log
    & powershell -NoProfile -Command "$cmd *>&1" 2>&1 | Tee-Object -FilePath $logFile -Append
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
        Write-Host "Comando finalizó con código: $exit" -ForegroundColor Yellow
    }
    return $exit
}

# Inicio del log
"=== INICIO DIAGNOSTICO - $timestamp ===" | Out-File -FilePath $logFile -Encoding utf8

# 1) Bajar contenedores previos de prod (limpiando orphans y volúmenes)
Run-Cmd "docker compose --profile $Profile down -v --remove-orphans"

# 2) Reconstruir (no-cache opcional si lo deseas)
Run-Cmd "docker compose --profile $Profile build --no-cache"

# 3) Levantar servicios
Run-Cmd "docker compose --profile $Profile up -d"

# 4) Espera breve para que los servicios arranquen
Start-Sleep -Seconds 4

# 5) Listar servicios del compose (si falla, caerá en lista por defecto)
$services = @()
try {
    $svcOut = & docker compose --profile $Profile ps --services 2>&1
    if ($svcOut) {
        $services = $svcOut -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    }
} catch {
    Write-Log "No se pudo listar servicios dinámicamente, se usará lista por defecto."
}

if (-not $services -or $services.Count -eq 0) {
    # fallback: servicios comunes que usa este proyecto
    $services = @("nginx", "nginx-prod", "nginx-dev", "backend", "backend-dev", "rasa", "action-server", "mongo", "redis")
}

"Servicios detectados para inspeccionar: $($services -join ', ')" | Write-Log

# 6) Recopilar logs por servicio (últimas $TailLines líneas)
foreach ($s in $services) {
    Write-Log ""
    Write-Log "------ LOG (servicio: $s) - Últimas $TailLines líneas ------"
    try {
        & docker compose --profile $Profile logs --tail $TailLines $s 2>&1 | Tee-Object -FilePath $logFile -Append
    } catch {
        Write-Log "No se pudieron obtener logs para servicio: $s"
    }
}

# 7) También guardar logs totales del compose (últimas $TailLines)
Write-Log ""
Write-Log "------ LOGS TOTALES docker compose --tail $TailLines ------"
Run-Cmd "docker compose --profile $Profile logs --tail $TailLines"

# 8) Buscar patrones críticos en el log
$patterns = @(
    "502 Bad Gateway",
    "SettingsError",
    "error parsing",
    "unhealthy",
    "Unhealthy",
    "Traceback",
    "Exception",
    "failed",
    "Connection refused",
    "Address already in use",
    "unknown \"connection_upgrade\" variable",
    "host not found in upstream"
)

Write-Log ""
Write-Log "------ ESCANEANDO LOG EN BUSCA DE PATRONES CRITICOS ------"
$matches = @()
foreach ($p in $patterns) {
    $m = Select-String -Path $logFile -Pattern $p -SimpleMatch -CaseSensitive:$false -ErrorAction SilentlyContinue
    if ($m) {
        $matches += $m
    }
}

# 9) Resultado y resumen
if ($matches.Count -eq 0) {
    Write-Host "NINGUN PATRON CRITICO ENCONTRADO." -ForegroundColor Green
    Write-Log "NINGUN PATRON CRITICO ENCONTRADO."
} else {
    Write-Host "SE ENCONTRARON PROBLEMAS (ver resumen abajo):" -ForegroundColor Red
    Write-Log "SE ENCONTRARON PROBLEMAS:"
    # Agrupar por patrón y mostrar pocas líneas de contexto
    $grouped = $matches | Group-Object -Property Pattern
    foreach ($g in $grouped) {
        Write-Host ""
        Write-Host ">>> Patron: $($g.Name) - ocurrencias: $($g.Count)" -ForegroundColor Yellow
        Write-Log ""
        Write-Log ">>> Patron: $($g.Name) - ocurrencias: $($g.Count)"
        $g.Group | Select-Object -First 20 | ForEach-Object {
            $line = "{0}:{1}: {2}" -f $_.Filename, $_.LineNumber, $_.Line.Trim()
            Write-Host $line -ForegroundColor White
            Write-Log $line
        }
    }
    Write-Log ""
    Write-Host "`nEl log completo está en: $logFile" -ForegroundColor Cyan
}

# 10) (Opcional) Mostrar logs en vivo si el usuario lo pidió
if ($FollowLive) {
    Write-Host "Abriendo logs en vivo (presiona Ctrl+C para salir)..." -ForegroundColor Cyan
    & docker compose --profile $Profile logs -f
}

Write-Host "FIN DEL SCRIPT. Archivo de log: $logFile" -ForegroundColor Cyan
"=== FIN DIAGNOSTICO - $(Get-Date -Format 'yyyyMMdd_HHmmss') ===" | Out-File -FilePath $logFile -Append -Encoding utf8
