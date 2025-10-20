@echo off
echo 🚀 Entrenando modelo Rasa...
rasa train

if %errorlevel% neq 0 (
    echo ❌ Error en el entrenamiento. Revisa tus archivos de NLU, rules o stories.
    pause
    exit /b %errorlevel%
)

echo 💬 Abriendo Rasa shell para pruebas...
rasa shell
pause