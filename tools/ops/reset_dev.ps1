# reset_dev_all.ps1
# Script unificado para reiniciar el entorno con Docker Compose (perfil build)
# Modos: menu | light | auto

param(
    [string]$Mode = "menu"
)

function Do-Down {
    Write-Host "[DOWN] Deteniendo y eliminando contenedores..." -ForegroundColor Red
    docker compose --profile build down
}

function Do-Prune {
    Write-Host "[PRUNE] Limpiando recursos huérfanos (volúmenes, redes, imágenes dangling)..." -ForegroundColor Yellow
    docker system prune -f --volumes
}

function Do-Up {
    Write-Host "[UP] Reconstruyendo y levantando contenedores (perfil build)..." -ForegroundColor Green
    docker compose --profile build up --build -d
}

function Do-Logs {
    Write-Host "`n[LOGS] Mostrando logs en tiempo real (Ctrl+C para salir):" -ForegroundColor Cyan
    docker compose --profile build logs -f
}

function Menu {
    do {
        Clear-Host
        Write-Host "============================" -ForegroundColor Cyan
        Write-Host "   Reset Dev - Docker Menu"
        Write-Host "============================" -ForegroundColor Cyan
        Write-Host "1) Detener y eliminar contenedores"
        Write-Host "2) Limpiar recursos huérfanos"
        Write-Host "3) Reconstruir y levantar"
        Write-Host "4) Ciclo completo (down + prune + up)"
        Write-Host "5) Ver estado de los contenedores"
        Write-Host "0) Salir"
        Write-Host "============================" -ForegroundColor Cyan

        $choice = Read-Host "Selecciona una opción"

        switch ($choice) {
            "1" { Do-Down; Read-Host "Presiona Enter para continuar..." | Out-Null }
            "2" { Do-Prune; Read-Host "Presiona Enter para continuar..." | Out-Null }
            "3" { Do-Up; Do-Logs }
            "4" { Do-Down; Do-Prune; Do-Up; Do-Logs }
            "5" { docker compose --profile build ps; Do-Logs }
            "0" { Write-Host "👋 Saliendo del menú..." -ForegroundColor Magenta }
            default { Write-Host "❌ Opción no válida, intenta de nuevo." -ForegroundColor Red }
        }
    } while ($choice -ne "0")
}

try {
    switch ($Mode.ToLower()) {
        "menu"  { Menu }
        "light" { Do-Down; Do-Prune; Do-Up; Do-Logs }
        "auto"  { Do-Down; Do-Prune; Do-Up; Write-Host "`n✅ Reset completo. Usa 'docker compose --profile build ps' para ver estado." -ForegroundColor Cyan }
        default { Write-Host "❌ Modo inválido. Usa: menu | light | auto" -ForegroundColor Red }
    }
}
catch {
    Write-Host "❌ Error ejecutando reset_dev_all.ps1: $_" -ForegroundColor Red
    exit 1
}