@echo off
cd /d %~dp0

REM Detener solo los servicios usados en el modo mixto
docker compose version >nul 2>&1
if %errorlevel%==0 (
  docker compose stop rasa rasa-actions mongo
) else (
  docker-compose stop rasa rasa-actions mongo
)

echo [OK] Servicios Docker detenidos (rasa, rasa-actions, mongo).
pause
