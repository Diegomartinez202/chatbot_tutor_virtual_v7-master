@echo off
setlocal enabledelayedexpansion

cd /d %~dp0

echo ======================================
echo  Chatbot Tutor Virtual - Health Check
echo ======================================

set FASTAPI=http://127.0.0.1:8000
set RASA=http://127.0.0.1:5005

set OK_FASTAPI=0
set OK_CHAT=0
set OK_RASA=0

echo [1/3] Comprobando FastAPI /ping ...
powershell -Command "try { $r = Invoke-WebRequest -UseBasicParsing %FASTAPI%/ping -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel%==0 (
  echo   [OK] %FASTAPI%/ping
  set OK_FASTAPI=1
) else (
  echo   [FAIL] %FASTAPI%/ping
)

echo [2/3] Comprobando FastAPI /chat/health ...
powershell -Command "try { $r = Invoke-WebRequest -UseBasicParsing %FASTAPI%/chat/health -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel%==0 (
  echo   [OK] %FASTAPI%/chat/health
  set OK_CHAT=1
) else (
  echo   [FAIL] %FASTAPI%/chat/health
)

echo [3/3] Comprobando Rasa /status ...
powershell -Command "try { $r = Invoke-WebRequest -UseBasicParsing %RASA%/status -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel%==0 (
  echo   [OK] %RASA%/status
  set OK_RASA=1
) else (
  echo   [FAIL] %RASA%/status
)

echo --------------------------------------
if %OK_FASTAPI%==1 if %OK_CHAT%==1 if %OK_RASA%==1 (
  echo  TODOS LOS SERVICIOS RESPONDEN OK
  start %FASTAPI%/docs
) else (
  echo  [ADVERTENCIA] Alguno de los servicios no respondio correctamente.
)
echo --------------------------------------

pause
endlocal
