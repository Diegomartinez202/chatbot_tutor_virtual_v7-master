Write-Host "=== Verificando entorno antes de levantar Docker ===`n"

# 1. Espacio en disco
$disk = Get-PSDrive -Name C
Write-Host "📂 Disco C: Usado $([math]::Round($disk.Used/1GB,2)) GB / Libre $([math]::Round($disk.Free/1GB,2)) GB"
if ($disk.Free -lt 5GB) {
    Write-Host "⚠️  Atención: Menos de 5GB libres en C:. Libera espacio antes de continuar." -ForegroundColor Red
    exit 1
}

# 2. Verificar que Docker Desktop esté corriendo
try {
    docker info | Out-Null
    Write-Host "🐳 Docker está corriendo correctamente."
}
catch {
    Write-Host "❌ Docker no está disponible. Abre Docker Desktop y espera a que diga 'Engine running'." -ForegroundColor Red
    exit 1
}

# 3. Revisar contenedores activos
Write-Host "`n🔎 Contenedores activos:"
docker ps

# 4. Intentar levantar proyecto
Write-Host "`n🚀 Levantando proyecto con perfil PROD..."
docker compose --profile prod up -d --build

Write-Host "`n✅ Script finalizado. Usa 'docker ps' para verificar que los contenedores estén arriba."