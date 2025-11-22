# ===============================
# 📜 ver_logs.ps1 - Monitor de Logs Interactivo
# ===============================

# Configuración inicial
Write-Host "`n🧠 MONITOR DE LOGS - PERFIL PRODUCCIÓN" -ForegroundColor Cyan
Write-Host "================================================="

# Definir los contenedores activos por nombre
$containers = @{
    "1" = "backend"
    "2" = "rasa"
    "3" = "action-server"
    "4" = "redis"
    "5" = "mongo"
    "6" = "nginx-prod"
    "7" = "Salir"
}

# Mostrar menú
Write-Host "`nSelecciona el servicio que deseas monitorear:`" -ForegroundColor Yellow
$containers.GetEnumerator() | ForEach-Object { Write-Host ("{0}. {1}" -f $_.Key, $_.Value) }

# Leer la opción del usuario
$choice = Read-Host "`n👉 Ingresa el número del servicio"

if ($containers.ContainsKey($choice)) {
    $service = $containers[$choice]

    if ($service -eq "Salir") {
        Write-Host "`n👋 Saliendo del monitor de logs..." -ForegroundColor Cyan
        exit
    }

    Write-Host "`n🚀 Mostrando logs del contenedor: $service" -ForegroundColor Green
    Write-Host "Presiona Ctrl + C para salir del modo de seguimiento." -ForegroundColor DarkGray
    Write-Host "=================================================`n"

    # Capturar logs en tiempo real
    try {
        docker logs -f --tail 100 $service 2>&1 |
        ForEach-Object {
            if ($_ -match "ERROR|Error|exception|502|failed|unhealthy|denied|refused") {
                Write-Host $_ -ForegroundColor Red
            }
            elseif ($_ -match "WARNING|warn|deprecated") {
                Write-Host $_ -ForegroundColor Yellow
            }
            elseif ($_ -match "INFO|success|ready|running|connected") {
                Write-Host $_ -ForegroundColor Green
            }
            else {
                Write-Host $_
            }
        }
    }
    catch {
        Write-Host "`n❌ No se pudieron obtener los logs del servicio $service" -ForegroundColor Red
    }
}
else {
    Write-Host "`n⚠️ Opción inválida. Intenta de nuevo." -ForegroundColor Red
}