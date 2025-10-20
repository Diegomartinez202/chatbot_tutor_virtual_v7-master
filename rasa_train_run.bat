@echo off
echo 🚀 Entrenando modelo Rasa...
rasa train

if %errorlevel% neq 0 (
    echo ❌ Error en el entrenamiento. Revisa tus archivos de NLU, rules o stories.
    pause
    exit /b %errorlevel%
)

echo 🌐 Levantando servidor Rasa en http://localhost:5005 ...
rasa run --enable-api --cors "*"
pause