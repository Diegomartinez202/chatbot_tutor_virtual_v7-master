@echo off
cd /d %~dp0
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend\requirements.txt --no-cache-dir
pause
