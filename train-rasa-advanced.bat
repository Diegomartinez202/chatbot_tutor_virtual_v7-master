@echo off
setlocal enabledelayedexpansion

echo === Validando datos Rasa ===
docker exec -it ctv_rasa rasa data validate --fail-on-warning
if %errorlevel% neq 0 (
    echo ❌ Error en validación de datos. Abortando entrenamiento.
    pause
    exit /b %errorlevel%
)

echo === Entrenando modelo Rasa con logs en tiempo real ===
docker exec -it ctv_rasa rasa train --verbose
if %errorlevel% neq 0 (
    echo ❌ Error durante el entrenamiento. Revisa los logs.
    pause
    exit /b %errorlevel%
)

echo ✅ Entrenamiento completado. Los modelos están en ./rasa/models
pause