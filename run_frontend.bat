@echo off
cd /d %~dp0\admin_panel_react
where npm >nul 2>&1 || (echo [ERROR] Node/NPM no estan en PATH. Instala Node.js LTS. & pause & exit /b 1)
echo [1/2] npm install...
call npm install
echo [2/2] npm run dev (http://localhost:5173)...
call npm run dev
pause
