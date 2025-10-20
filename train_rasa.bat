@echo off
echo === Validando datos Rasa ===
docker exec -it ctv_rasa rasa data validate --fail-on-warning
if %errorlevel% neq 0 (
    echo ❌ Error en validacion de datos
    pause
    exit /b %errorlevel%
)

echo === Entrenando modelo Rasa ===
docker exec -it ctv_rasa rasa train
if %errorlevel% neq 0 (
    echo ❌ Error en entrenamiento de modelo
    pause
    exit /b %errorlevel%
)

echo ✅ Entrenamiento completado. Los modelos están en ./rasa/models
pause