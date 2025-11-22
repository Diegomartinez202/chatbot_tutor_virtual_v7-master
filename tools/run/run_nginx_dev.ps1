function Menu {
    Write-Host "=== Nginx-dev Menu ===" -ForegroundColor Cyan
    Write-Host "[1] Levantar nginx-dev"
    Write-Host "[2] Ver logs nginx-dev"
    Write-Host "[3] Reiniciar nginx-dev"
    Write-Host "[4] Apagar nginx-dev"
    Write-Host "[0] Salir"
    $option = Read-Host "Selecciona opcion"

    switch ($option) {
        "1" { docker compose --profile build up -d --build nginx-dev }
        "2" { docker compose logs -f nginx-dev }
        "3" { docker compose restart nginx-dev }
        "4" { docker compose stop nginx-dev }
        "0" { exit }
    }
    Menu
}
Menu