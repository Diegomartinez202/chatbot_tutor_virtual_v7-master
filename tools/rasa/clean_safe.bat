@echo off
echo === Limpieza segura de Docker + Modelos de Rasa ===

:: 1) Borrar imágenes dangling
echo → Borrando imagenes dangling...
docker image prune -f

:: 2) Borrar build cache
echo → Borrando cache de build...
docker builder prune -f

:: 3) Borrar modelos viejos de Rasa dejando solo 3
set "modelsPath=rasa\models"
if exist "%modelsPath%" (
    echo → Revisando modelos en %modelsPath%...
    set count=0
    for /f "delims=" %%a in ('dir /b /o-d /a-d "%modelsPath%\*.tar.gz"') do (
        set /a count+=1
        if !count! gtr 3 (
            echo Borrando %%a
            del "%modelsPath%\%%a"
        )
    )
    echo ✅ Limpieza de modelos completa (se conservaron los 3 mas recientes).
) else (
    echo ⚠️ No se encontro la carpeta %modelsPath%.
)

echo === Limpieza finalizada ===
pause