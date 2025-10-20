# === Libera espacio y memoria para DEV (Docker + WSL + Proyecto) ===
Write-Host "ðŸ”§ Cerrando Docker y WSL..." -ForegroundColor Cyan
Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force
wsl --shutdown
Restart-Service LxssManager -ErrorAction SilentlyContinue

Write-Host "ðŸ§¹ Limpiando Docker (conservador)..." -ForegroundColor Cyan
docker system prune -f
docker builder prune -f
docker image prune -f
docker container prune -f
docker network prune -f

Write-Host "ðŸ§¹ Limpiando caches del proyecto..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot"
if (Test-Path .\admin_panel_react\node_modules) { Remove-Item .\admin_panel_react\node_modules -Recurse -Force }
npm --prefix .\admin_panel_react cache clean --force 2>$null
pip cache purge 2>$null
Get-ChildItem -Recurse -Include __pycache__,.pytest_cache,.mypy_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path .\.venv) { Remove-Item .\.venv -Recurse -Force }

Write-Host "ðŸ§¹ Limpiando temporales Windows..." -ForegroundColor Cyan
Get-ChildItem "$env:TEMP" -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "âš™ï¸  (Opcional) Compactar VHDX de Docker si existe..." -ForegroundColor Yellow
$ddd = "$env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx"
if (Test-Path $ddd) {
  try { Optimize-VHD -Path $ddd -Mode Full } catch { Write-Host "  - Saltando compactaciÃ³n (falta Hyper-V): $_" -ForegroundColor DarkYellow }
}

Write-Host "ðŸš€ Reiniciando Docker..." -ForegroundColor Cyan
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Start-Sleep -Seconds 60
docker context use default | Out-Null

Write-Host "ðŸ“¦ Levantando perfil build..." -ForegroundColor Cyan
docker compose --profile build up -d
docker compose --profile build ps

Write-Host "âœ… Listo. Verifica Rasa/Backend vÃ­a Nginx: http://localhost:8080/" -ForegroundColor Green