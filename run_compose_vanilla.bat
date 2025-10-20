@echo off
setlocal
cd /d %~dp0

REM Perfil que usa IMAGENES OFICIALES (ctv_*) montando tu codigo
set PROFILE=vanilla

where docker >nul 2>&1 || (echo [ERROR] Docker no esta en PATH. Instala/abre Docker Desktop. & pause & exit /b 1)

if "%~1"=="" goto :menu

if /I "%~1"=="up"       goto :up
if /I "%~1"=="down"     goto :down
if /I "%~1"=="logs"     goto :logs
if /I "%~1"=="rebuild"  goto :rebuild

:menu
echo ===========================
echo  docker compose (vanilla)
echo ===========================
echo 1) up       (levantar)
echo 2) down     (apagar)
echo 3) logs     (ver logs)
echo 4) rebuild  (reconstruir)
echo.
choice /c 1234 /n /m "Elige opcion: "
if errorlevel 4 goto :rebuild
if errorlevel 3 goto :logs
if errorlevel 2 goto :down
if errorlevel 1 goto :up

:up
docker compose --profile %PROFILE% up -d --build
goto :end

:down
docker compose --profile %PROFILE% down
goto :end

:logs
echo [INFO] Presiona CTRL+C para salir de logs...
docker compose --profile %PROFILE% logs -f
goto :end

:rebuild
docker compose --profile %PROFILE% build --no-cache
docker compose --profile %PROFILE% up -d
goto :end

:end
echo.
echo [OK] Comando finalizado para perfil "%PROFILE%".
pause
endlocal
