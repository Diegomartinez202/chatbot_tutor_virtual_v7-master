@echo off
echo ==============================
echo   Iniciando Chatbot Backend
echo ==============================
cd /d "%~dp0"
call backend\.venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
pause