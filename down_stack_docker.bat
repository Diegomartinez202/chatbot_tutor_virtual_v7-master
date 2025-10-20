@echo off
cd /d %~dp0
docker compose version >nul 2>&1
if %errorlevel%==0 (
  docker compose down
) else (
  docker-compose down
)
echo [OK] Stack detenido.
pause
