@echo off
echo ===================================
echo   Iniciando Chatbot (Backend + Frontend)
echo ===================================

:: Iniciar Backend en nueva ventana
start "Backend" cmd /k "cd /d %~dp0 & call backend\.venv\Scripts\activate & uvicorn backend.main:app --reload --port 8000"

:: Iniciar Frontend en nueva ventana
start "Frontend" cmd /k "cd /d %~dp0\frontend & npm run dev"

echo ===================================
echo   Todo iniciado. Cierra esta ventana.
echo ===================================
pause