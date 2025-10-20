# ======================================================================
# CLEAN DOCKER FOLDERS (PowerShell)
# Limpia carpetas temporales, logs y caches de Docker Desktop en Windows
# sin eliminar imagenes o contenedores activos.
# ======================================================================

# Sugerencia: Ejecuta esta consola como Administrador
Write-Host "Iniciando limpieza de carpetas temporales de Docker..." -ForegroundColor Cyan

# Rutas tipicas de Docker Desktop en Windows
$folders = @(
    "$env:LOCALAPPDATA\Docker\log",
    "$env:LOCALAPPDATA\Docker\run",
    "$env:LOCALAPPDATA\Docker\tmp",
    "$env:LOCALAPPDATA\DockerDesktop\log",
    "$env:LOCALAPPDATA\DockerDesktop\run",
    "$env:LOCALAPPDATA\DockerDesktop\tmp"
)

foreach ($folder in $folders) {
    if (Test-Path -LiteralPath $folder) {
        try {
            Write-Host "Limpiando: $folder" -ForegroundColor Yellow
            Get-ChildItem -LiteralPath $folder -Recurse -Force -ErrorAction SilentlyContinue |
                Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Limpieza completada: $folder" -ForegroundColor Green
        }
        catch {
            Write-Host "No se pudo limpiar $folder : $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Carpeta no encontrada (omitida): $folder" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Limpieza de carpetas Docker completada." -ForegroundColor Cyan
Write-Host "Si deseas liberar aun mas espacio, ejecuta luego manualmente:" -ForegroundColor Yellow
Write-Host "    docker system prune -a" -ForegroundColor Magenta