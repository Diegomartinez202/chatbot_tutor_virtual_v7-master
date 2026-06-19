# ===============================
# 🔍 Check rápido de NGINX
# Archivo: check-nginx.ps1
# Uso: .\check-nginx.ps1
# ===============================

Write-Host "🚀 Verificando contenedor NGINX..."

# 1. Verificar si el contenedor está corriendo
$nginx = docker ps --filter "name=nginx" --format "{{.Names}}"
if (-not $nginx) {
    Write-Host "❌ NGINX no está corriendo."
    exit 1
} else {
    Write-Host "✅ NGINX está corriendo: $nginx"
}

# 2. Verificar puertos
Write-Host "🔌 Puertos expuestos:"
docker port $nginx

# 3. Verificar respuesta HTTP
try {
    $response = Invoke-WebRequest -Uri http://localhost -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ NGINX responde correctamente en http://localhost"
    } else {
        Write-Host "⚠️ NGINX respondió con código: $($response.StatusCode)"
    }
} catch {
    Write-Host "❌ No se pudo conectar a http://localhost"
}