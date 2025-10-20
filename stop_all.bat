@echo off
REM Intenta cerrar las ventanas abiertas por run_all.bat
taskkill /FI "WINDOWTITLE eq BACKEND FastAPI" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq FRONTEND React/Vite" /F >nul 2>&1
echo [OK] Intento de cierre enviado. Si quedan procesos, cierra con CTRL+C.
pause
