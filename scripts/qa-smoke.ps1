param(
  [string]$HostBase = "http://localhost"
)

function Test-Endpoint($Name, $Url) {
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
      Write-Host "✅ $Name: $($resp.StatusCode)" -ForegroundColor Green
      return $true
    } else {
      Write-Host "❌ $Name: $($resp.StatusCode)" -ForegroundColor Red
      return $false
    }
  } catch {
    Write-Host "❌ $Name: $($_.Exception.Message)" -ForegroundColor Red
    return $false
  }
}

$ok = $true
$ok = (Test-Endpoint "Admin UI"        "$HostBase/") -and $ok
$ok = (Test-Endpoint "FastAPI /docs"   "$HostBase`:8000/docs") -and $ok
$ok = (Test-Endpoint "Rasa /status"    "$HostBase`:5005/status") -and $ok
$ok = (Test-Endpoint "Actions /health" "$HostBase`:5055/health") -and $ok

# Ping al bot
try {
  $payload = @{ sender = "qa_smoke"; message = "hola" } | ConvertTo-Json
  $resp = Invoke-RestMethod -Uri "$HostBase`:5005/webhooks/rest/webhook" -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 10
  if ($resp) {
    Write-Host "✅ Rasa webhook respondió con $(($resp | ConvertTo-Json -Depth 5).Length) chars" -ForegroundColor Green
  } else {
    Write-Host "❌ Rasa webhook sin contenido" -ForegroundColor Red
    $ok = $false
  }
} catch {
  Write-Host "❌ Rasa webhook error: $($_.Exception.Message)" -ForegroundColor Red
  $ok = $false
}

if ($ok) {
  Write-Host "`n✅ SMOKE OK — todo responde" -ForegroundColor Green
  exit 0
} else {
  Write-Host "`n❌ SMOKE FAIL — revisa logs" -ForegroundColor Red
  exit 1
}