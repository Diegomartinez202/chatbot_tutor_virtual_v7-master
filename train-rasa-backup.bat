@echo off
setlocal enabledelayedexpansion

REM Carpeta de modelos
set MODEL_DIR=.\rasa\models
set BACKUP_DIR=.\rasa\models_backup

REM Crear carpeta de backup si no existe
if not exist "!BACKUP_DIR!" mkdir "!BACKUP_DIR!"

REM Crear timestamp para el backup
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do (
    set DATE=%%c%%a%%b
)
for /f "tokens=1-2 delims=: " %%a in ("%time%") do (
    set TIME=%%a%%b
)
set TIMESTAMP=!DATE!_!TIME!

REM Hacer backup de modelos existentes
if exist "!MODEL_DIR!\*" (
    echo 📦 Haciendo backup de modelos existentes...
    xcopy /E /I /Y "!MODEL_DIR!\*" "!BACKUP_DIR!\backup_!TIMESTAMP!\"
    echo ✅ Backup completado en "!BACKUP_DIR!\backup_!TIMESTAMP!"
) else (
    echo ⚠️ No se encontraron modelos existentes para backup
)

REM Validar datos Rasa
echo === Validando datos Rasa ===
docker exec -it ctv_rasa rasa data validate --fail-on-warning
if %errorlevel% neq 0 (
    echo ❌ Error en validación de datos. Abortando entrenamiento.
    pause
    exit /b %errorlevel%
)

REM Entrenar modelo con logs en tiempo real
echo === Entrenando modelo Rasa ===
docker exec -it ctv_rasa rasa train --verbose
if %errorlevel% neq 0 (
    echo ❌ Error durante el entrenamiento. Revisa los logs.
    pause
    exit /b %errorlevel%
)

echo ✅ Entrenamiento completado. Los modelos están en ./rasa/models
pause