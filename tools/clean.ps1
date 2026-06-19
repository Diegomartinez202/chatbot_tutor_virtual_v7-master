param(
    [ValidateSet("docker","docker-folders","rasa","yaml","all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Chatbot Tutor Virtual - CLEAN TOOL  " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Target: $Target"
Write-Host ""

function Clean-Docker {
    Write-Host "🧹 Limpieza de Docker (imágenes, contenedores, volúmenes, redes)..." -ForegroundColor Yellow

    Write-Host "  → Limpiando caché de compilación..." -ForegroundColor DarkYellow
    docker builder prune -f

    Write-Host "  → Eliminando imágenes obsoletas (no usadas)..." -ForegroundColor DarkYellow
    docker image prune -a -f

    Write-Host "  → Eliminando contenedores detenidos..." -ForegroundColor DarkYellow
    docker container prune -f

    Write-Host "  → Eliminando volúmenes huérfanos..." -ForegroundColor DarkYellow
    docker volume prune -f

    Write-Host "  → Eliminando redes no usadas..." -ForegroundColor DarkYellow
    docker network prune -f

    Write-Host ""
    Write-Host "✅ Limpieza Docker completada. Estado actual:" -ForegroundColor Green
    docker system df
    Write-Host ""
}

function Clean-DockerFolders {
    Write-Host "🧹 Limpieza de carpetas temporales de Docker Desktop (Windows)..." -ForegroundColor Yellow

    $folders = @(
        "$env:LOCALAPPDATA\Docker\log",
        "$env:LOCALAPPDATA\Docker\run",
        "$env:LOCALAPPDATA\Docker\tmp",
        "$env:LOCALAPPDATA\DockerDesktop\log",
        "$env:LOCALAPPDATA\DockerDesktop\run",
        "$env:LOCALAPPDATA\DockerDesktop\tmp"
    )

    foreach ($folder in $folders) {
        if (Test-Path -LiteralPath $folder) {
            try {
                Write-Host "  → Limpiando: $folder" -ForegroundColor DarkYellow
                Get-ChildItem -LiteralPath $folder -Recurse -Force -ErrorAction SilentlyContinue |
                    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "     OK: $folder" -ForegroundColor Green
            } catch {
                Write-Host "     Error limpiando $folder : $_" -ForegroundColor Red
            }
        } else {
            Write-Host "  (omitido, no existe): $folder" -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    Write-Host "✅ Limpieza de carpetas Docker Desktop completada." -ForegroundColor Green
    Write-Host "Si deseas liberar aún más espacio, ejecuta manualmente:" -ForegroundColor Yellow
    Write-Host "    docker system prune -a" -ForegroundColor Magenta
    Write-Host ""
}

function Clean-RasaModels {
    Write-Host "🧹 Limpieza segura de modelos de Rasa + Docker cache..." -ForegroundColor Yellow

    # 1) Imágenes dangling
    Write-Host "  → Borrando imágenes dangling..." -ForegroundColor DarkYellow
    docker image prune -f

    # 2) Caché de build
    Write-Host "  → Borrando caché de build de Docker..." -ForegroundColor DarkYellow
    docker builder prune -f

    # 3) Modelos de Rasa (dejar solo 3 más recientes)
    $modelsPath = "rasa\models"
    Write-Host "  → Revisando modelos en $modelsPath ..." -ForegroundColor DarkYellow

    if (Test-Path $modelsPath) {
        $files = Get-ChildItem $modelsPath -Filter "*.tar.gz" | Sort-Object LastWriteTime -Descending

        if ($files.Count -le 3) {
            Write-Host "  Solo hay $($files.Count) modelos, no se borra nada." -ForegroundColor Green
        } else {
            $toDelete = $files | Select-Object -Skip 3
            foreach ($f in $toDelete) {
                Write-Host "  Borrando $($f.Name)" -ForegroundColor Red
                Remove-Item $f.FullName -Force
            }
            Write-Host "  ✅ Limpieza de modelos completa (se conservaron los 3 más recientes)." -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠️ No se encontró la carpeta $modelsPath" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "✅ Limpieza Rasa completada." -ForegroundColor Green
    Write-Host ""
}

function Clean-Yaml {
    Write-Host "🧹 Limpieza de YAML dentro del contenedor Rasa..." -ForegroundColor Yellow

    # Comprobar si el contenedor 'rasa' está corriendo
    $rasaRunning = docker ps --format '{{.Names}}' | Select-String -SimpleMatch "rasa"
    if (-not $rasaRunning) {
        Write-Host "❌ El contenedor 'rasa' no está en ejecución. Inícialo antes de continuar." -ForegroundColor Red
        return
    }

    # Asumimos que clean_yaml.py está montado en /app/clean_yaml.py dentro del contenedor
    Write-Host "  → Ejecutando clean_yaml.py dentro del contenedor 'rasa'..." -ForegroundColor DarkYellow
    docker exec rasa python /app/tools/maintenance/clean_yaml.py

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Limpieza de YAML completada." -ForegroundColor Green
    } else {
        Write-Host "⚠️ Hubo algún problema al ejecutar clean_yaml.py dentro de 'rasa'." -ForegroundColor Yellow
    }

    Write-Host ""
}

switch ($Target) {
    "docker" {
        Clean-Docker
    }
    "docker-folders" {
        Clean-DockerFolders
    }
    "rasa" {
        Clean-RasaModels
    }
    "yaml" {
        Clean-Yaml
    }
    "all" {
        Clean-Docker
        Clean-DockerFolders
        Clean-RasaModels
        Clean-Yaml
    }
}

Write-Host "✨ Proceso de limpieza terminado." -ForegroundColor Cyan
