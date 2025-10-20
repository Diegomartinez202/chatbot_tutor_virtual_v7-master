@echo off
cd /d %~dp0
if not exist ".venv\Scripts\activate.bat" (
echo [INFO] No existe .venv, creando...
python -m venv .venv
)
start "BACKEND FastAPI" cmd /k "call .venv\Scripts\activate && .venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel && (if exist backend\requirements.txt (.venv\Scripts\python.exe -m pip install -r backend\requirements.txt --no-cache-dir) else (.venv\Scripts\python.exe -m pip install fastapi uvicorn)) && .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
if not exist "admin_panel_react\package.json" (
echo [ERROR] No encuentro admin_panel_react\package.json
pause & exit /b 1
)
start "FRONTEND React/Vite" cmd /k "cd /d %~dp0\admin_panel_react && npm -v || (echo [ERROR] Node/NPM no estan en PATH. & pause & exit /b 1) && npm install && npm run dev"
echo [OK] Abiertas dos ventanas: Backend http://127.0.0.1:8000/docs y Frontend http://localhost:5173
