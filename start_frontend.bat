@echo off
echo ==============================
echo   Iniciando Chatbot Frontend
echo ==============================
cd /d "%~dp0\frontend"
npm install
npm run dev
pause