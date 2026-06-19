@echo off
cd /d %~dp0

REM --- Comprobaciones basicas ---
where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop no esta instalado o no esta en PATH.
  echo Descargalo desde: https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

REM --- Crear .env.docker si no existe ---
if not exist ".env.docker" (
  echo Creando .env.docker por primera vez...
  > .env.docker echo MONGO_INITDB_ROOT_USERNAME=admin
  >> .env.docker echo MONGO_INITDB_ROOT_PASSWORD=admin123
  >> .env.docker echo MONGO_DB=chatbot
  >> .env.docker echo FASTAPI_PORT=8000
  >> .env.docker echo RASA_PORT=5005
)

REM --- Usar compose v2 (docker compose) o v1 (docker-compose) ---
docker compose version >nul 2>&1
if %errorlevel%==0 (
  docker compose --env-file .env.docker up -d --build
) else (
  docker-compose --env-file .env.docker up -d --build
)

echo.
echo [OK] Stack arriba:
echo   FastAPI:  http://127.0.0.1:8000/docs
echo   Rasa:     http://127.0.0.1:5005/status
echo   MongoDB:  mongodb://admin:admin123@127.0.0.1:27017/
echo.
pause
