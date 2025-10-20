@echo off
REM === Activar entorno virtual y correr FastAPI ===

cd /d %~dp0
echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo Iniciando servidor Uvicorn en http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
