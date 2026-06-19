param(
  [string]$FastApiUrl = "http://127.0.0.1:8000",
  [string]$RasaUrl    = "http://127.0.0.1:5005",
  [string]$ActionsUrl = "http://127.0.0.1:5055",
  [switch]$OpenDocs
)

$ErrorActionPreference = "SilentlyContinue"

function Test-Endpoint {
  param([string]$Url, [string]$Name)
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $res = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri $Url
    $sw.Stop()
    if ($res.StatusCode -eq 200) {
      Write-Host ("[OK]  {0}  {1}ms" -f $Url, $sw.ElapsedMilliseconds) -ForegroundColor Green
      return @{ ok=$true; ms=$sw.ElapsedMilliseconds; name=$Name }
    } else {
      Write-Host ("[FAIL]{0}  {1}" -f (" " * 2), $Url) -ForegroundColor Red
      return @{ ok=$false; ms=$sw.ElapsedMilliseconds; name=$Name }
    }
  } catch {
    $sw.Stop()
    Write-Host ("[FAIL] {0} ({1}ms)" -f $Url, $sw.ElapsedMilliseconds) -ForegroundColor Red
    return @{ ok=$false; ms=$sw.ElapsedMilliseconds; name=$Name }
  }
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Chatbot Tutor Virtual - Health Check " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$fastapiPing   = Test-Endpoint -Url "$FastApiUrl/ping"        -Name "fastapi_ping"
$chatHealth    = Test-Endpoint -Url "$FastApiUrl/chat/health" -Name "chat_health"
$rasaStatus    = Test-Endpoint -Url "$RasaUrl/status"         -Name "rasa_status"
$actionsHealth = Test-Endpoint -Url "$ActionsUrl/health"      -Name "actions_health"

$allOk = $fastapiPing.ok -and $chatHealth.ok -and $rasaStatus.ok -and $actionsHealth.ok
Write-Host "--------------------------------------"
if ($allOk) {
  Write-Host "TODOS LOS SERVICIOS RESPONDEN OK" -ForegroundColor Green
  if ($OpenDocs) { Start-Process "$FastApiUrl/docs" }
} else {
  Write-Host "ALGUN SERVICIO FALLÓ (ver arriba)" -ForegroundColor Yellow
}
Write-Host "--------------------------------------"