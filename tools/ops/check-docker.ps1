Write-Host "=== Verificando entorno antes de levantar Docker ===`n"

# ==============================
# 1. Espacio en disco
# ==============================
$disk = Get-PSDrive -Name C
Write-Host "📂 Disco C: Usado $([math]::Round($disk.Used/1GB,2)) GB / Libre $([math]::Round($disk.Free/1GB,2)) GB"
if ($disk.Free -lt 5GB) {
    Write-Host "⚠️  Atención: Menos de 5GB libres en C:. Libera espacio antes de continuar." -ForegroundColor Red
    exit 1
}

# ==============================
# 2. Verificar Docker Desktop
# ==============================
try {
    docker info | Out-Null
    Write-Host "🐳 Docker está corriendo correctamente."
}
catch {
    Write-Host "❌ Docker no está disponible. Abre Docker Desktop y espera a que diga 'Engine running'." -ForegroundColor Red
    exit 1
}

# ==============================
# 3. Contenedores activos
# ==============================
Write-Host "`n🔎 Contenedores activos actualmente:"
docker ps

# ==============================
# 4. Levantar proyecto
# ==============================
Write-Host "`n🚀 Levantando proyecto con perfil PROD..."
docker compose --profile prod up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al ejecutar docker compose. Revisa tu archivo docker-compose.yml" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 5

# ==============================
# 5. Verificar estado de contenedores
# ==============================
Write-Host "`n🔎 Verificando estado de contenedores tras el arranque..."
$containers = docker ps -a --format "{{.Names}}: {{.Status}}"

foreach ($c in $containers) {
    Write-Host " - $c"
}

# ==============================
# 6. Mostrar logs y reiniciar si falla
# ==============================
$failed = docker ps -a --filter "status=exited" --format "{{.Names}}"

if ($failed) {
    Write-Host "`n⚠️  Los siguientes contenedores fallaron:" -ForegroundColor Yellow
    foreach ($f in $failed) {
        Write-Host "   → $f" -ForegroundColor Red
        Write-Host "`n📜 Logs de $f:" -ForegroundColor Cyan
        docker logs --tail 50 $f
        Write-Host "`n🔄 Intentando reiniciar $f..." -ForegroundColor Yellow
        docker restart $f | Out-Null
        Start-Sleep -Seconds 3
        $status = docker ps --filter "name=$f" --format "{{.Status}}"
        if ($status) {
            Write-Host "✅ $f reiniciado correctamente → $status" -ForegroundColor Green
        } else {
            Write-Host "❌ No se pudo reiniciar $f, revisa manualmente." -ForegroundColor Red
        }

        # 🚨 Caso especial: si nginx falla
        if ($f -match "nginx") {
            Write-Host "`n⚠️ Detectado fallo en Nginx → reconstruyendo..." -ForegroundColor Yellow
            docker compose --profile prod up -d --build nginx
            Start-Sleep -Seconds 5
            $nginxStatus = docker ps --filter "name=nginx" --format "{{.Status}}"
            if ($nginxStatus) {
                Write-Host "✅ Nginx reconstruido y corriendo → $nginxStatus" -ForegroundColor Green
            } else {
                Write-Host "❌ Nginx sigue fallando, revisa logs con: docker logs nginx" -ForegroundColor Red
            }
        }

        Write-Host "`n-----------------------------------------`n"
    }
}
else {
    Write-Host "`n✅ Todos los contenedores están corriendo correctamente." -ForegroundColor Green
}

Write-Host "`n✨ Proceso finalizado. Usa 'docker ps' para verificar los servicios manualmente si lo deseas."