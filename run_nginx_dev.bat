@echo off
:menu
echo === Nginx-dev Menu ===
echo [1] Levantar nginx-dev
echo [2] Ver logs nginx-dev
echo [3] Reiniciar nginx-dev
echo [4] Apagar nginx-dev
echo [0] Salir
set /p option=Selecciona opcion: 

if "%option%"=="1" docker compose --profile build up -d --build nginx-dev
if "%option%"=="2" docker compose logs -f nginx-dev
if "%option%"=="3" docker compose restart nginx-dev
if "%option%"=="4" docker compose stop nginx-dev
if "%option%"=="0" exit
goto menu
