@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

REM ============================================================
REM  Chatbot Tutor Virtual v7.3 - RUN FULLSTACK (Mixto) v2
REM  - Levanta: Mongo + Rasa + Action Server (Docker)
REM  - Corre:   FastAPI (Uvicorn) en tu .venv local
REM  AUTO: intenta perfil "vanilla" primero; si falla, intenta "build"
REM  Puedes forzar: run_fullstack.bat vanilla  |  run_fullstack.bat build
REM ============================================================

set CHOSEN_PROFILE=
if /I "%~1"=="vanilla" set CHOSEN_PROFILE=vanilla
if /I "%~1"=="build"   set CHOSEN_PROFILE=build

where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop no esta instalado o no esta en PATH.
  pause
  exit /b 1
)

REM --- crear .env.docker si no existe ---
if not exist ".env.docker" (
  > .env.docker echo MONGO_INITDB_ROOT_USERNAME=admin
  >> .env.docker echo MONGO_INITDB_ROOT_PASSWORD=admin123
  >> .env.docker echo MONGO_DB=chatbot
  >> .env.docker echo FASTAPI_PORT=8000
  >> .env.docker echo RASA_PORT=5005
)

REM --- funcion para levantar un perfil ---
set "UP_OK=0"
set "PROFILE_TRIED="
for %%P in (%CHOSEN_PROFILE% auto) do (
  if /I "%%P"=="build" (
    echo [INFO] Intentando perfil build (mongo, rasa, action-server)...
    docker compose --profile build up -d --build mongo rasa action-server
    if !errorlevel! EQU 0 ( set "UP_OK=1" & set "PROFILE_TRIED=build" & goto :after_up )
  ) else if /I "%%P"=="vanilla" (
    echo [INFO] Intentando perfil vanilla (ctv_mongo, ctv_rasa, ctv_rasa_actions)...
    docker compose --profile vanilla up -d --build ctv_mongo ctv_rasa ctv_rasa_actions
    if !errorlevel! EQU 0 ( set "UP_OK=1" & set "PROFILE_TRIED=vanilla" & goto :after_up )
  ) else if /I "%%P"=="auto" (
    REM AUTO: primero vanilla
    echo [INFO] AUTO: probando vanilla...
    docker compose --profile vanilla up -d --build ctv_mongo ctv_rasa ctv_rasa_actions
    if !errorlevel! EQU 0 ( set "UP_OK=1" & set "PROFILE_TRIED=vanilla" & goto :after_up )
    echo [INFO] AUTO: vanilla fallo, probando build...
    docker compose --profile build up -d --build mongo rasa action-server
    if !errorlevel! EQU 0 ( set "UP_OK=1" & set "PROFILE_TRIED=build" & goto :after_up )
  )
)

:after_up
if "%UP_OK%"=="0" (
  echo [ERROR] Fallo al levantar servicios Docker. Revisa nombres de servicio en docker-compose.yml.
  echo         Usa manualmente:  docker compose --profile vanilla up -d --build ctv_mongo ctv_rasa ctv_rasa_actions
  echo         o:                 docker compose --profile build   up -d --build mongo rasa action-server
  pause
  exit /b 1
)

echo [OK] Servicios Docker arriba con perfil: %PROFILE_TRIED%

REM --- Espera a que Rasa (5005) y Mongo (27017) respondan ---
echo [INFO] Esperando a que Rasa y Mongo esten listos (~60s)...
set "READY_RASA=0"
set "READY_MONGO=0"
for /l %%I in (1,1,30) do (
  powershell -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5005/status -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
  if !errorlevel! == 0 set "READY_RASA=1"
  powershell -Command "try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',27017); if ($c.Connected){$c.Close(); exit 0}else{exit 1} } catch { exit 1 }"
  if !errorlevel! == 0 set "READY_MONGO=1"
  if "!READY_RASA!"=="1" if "!READY_MONGO!"=="1" goto :ready
  timeout /t 2 >nul
)

:ready
if not "!READY_RASA!"=="1" ( echo [WARN] Rasa no confirmo /status a tiempo. )
if not "!READY_MONGO!"=="1" ( echo [WARN] Mongo no confirmo TCP 27017 a tiempo. )

REM --- Backend local en .venv ---
if not exist ".venv\Scripts\activate.bat" (
  echo [INFO] No existe .venv, creando...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual .venv
    pause
    exit /b 1
  )
)

echo [INFO] Activando .venv e instalando deps minimas...
call .venv\Scripts\activate.bat
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if exist "backend\requirements.txt" (
  .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt --no-cache-dir
) else (
  .\.venv\Scripts\python.exe -m pip install fastapi uvicorn
)

echo [OK] Iniciando FastAPI en http://127.0.0.1:8000 ...
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo [INFO] Para apagar contenedores:  docker compose down
echo.
pause
endlocal