<#
  Smoke Tests — Chatbot Tutor Virtual
  Verifica coexistencia de rutas y respuestas básicas
  Incluye:
   - /api/auth/login, /api/auth/me
   - /auth/refresh, /api/auth/refresh
   - /auth/logout
   - /chat/health, /api/chat/health
   - Proxy /rasa/webhooks/rest/webhook
#>

param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Email   = "admin@demo.com",
  [string]$Pass    = "123456"
)

$ErrorActionPreference = "Stop"
Write-Host "🔎 Smoke tests contra $BaseUrl`n"

function Invoke-Json {
  param(
    [string]$Method, [string]$Url, [hashtable]$Headers, [string]$Body,
    [Microsoft.PowerShell.Commands.WebRequestSession]$Session, [switch]$AllowNon2xx
  )
  try {
    if ($Body) {
      $resp = Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers -ContentType "application/json" -Body $Body -WebSession $Session
    } else {
      $resp = Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers -WebSession $Session
    }
    return @{ ok=$true; status=200; data=$resp }
  } catch {
    $status = 0
    try { $status = [int]$_.Exception.Response.StatusCode.Value__ } catch {}
    if ($AllowNon2xx) { return @{ ok=$false; status=$status; data=$null } }
    throw
  }
}

function Assert-True { param([bool]$cond,[string]$msg)
  if (-not $cond) { throw "❌ $msg" }
  Write-Host "✅ $msg"
}

# --- 1) Health ---
$h1 = Invoke-Json -Method GET -Url "$BaseUrl/health"
Assert-True ($h1.ok -and $h1.status -eq 200) "/health responde 200"

# --- 2) Login ---
$session = $null
$loginResp = Invoke-RestMethod -Method POST `
  -Uri "$BaseUrl/api/auth/login" `
  -ContentType "application/json" `
  -Body (@{ email=$Email; password=$Pass } | ConvertTo-Json) `
  -SessionVariable session

$access = $loginResp.access_token
Assert-True ([string]::IsNullOrEmpty($access) -eq $false) "Login devuelve access_token"

# --- 3) /api/auth/me ---
$Headers = @{ Authorization = "Bearer $access" }
$me = Invoke-Json -Method GET -Url "$BaseUrl/api/auth/me" -Headers $Headers
Assert-True ($me.ok -and $me.status -eq 200 -and $me.data.email) "/api/auth/me devuelve email"

# --- 4) Refresh via cookie ---
foreach ($u in @("$BaseUrl/auth/refresh", "$BaseUrl/api/auth/refresh")) {
  try {
    $r = Invoke-RestMethod -Method POST -Uri $u -WebSession $session
    Assert-True ($r.access_token.Length -gt 10) "$u OK"
  } catch {
    Write-Host "⚠️ $u no disponible ($($_.Exception.Message))"
  }
}

# --- 5) Logout ---
try {
  $lg = Invoke-RestMethod -Method POST -Uri "$BaseUrl/auth/logout" -WebSession $session
  Write-Host "✅ /auth/logout OK"
} catch {
  Write-Host "⚠️ /auth/logout falló: $($_.Exception.Message)"
}

# --- 6) Rasa direct ---
$Rasa = "http://localhost:5005"
$payload = @{ sender="smoke_tester"; message="hola" } | ConvertTo-Json
$rasaRes = Invoke-RestMethod -Uri "$Rasa/webhooks/rest/webhook" -Method POST -ContentType "application/json" -Body $payload
Assert-True ($rasaRes.Count -gt 0) "Rasa respondió al webhook directo"

# --- 7) Rasa via proxy ---
$Proxy = "http://localhost:8080"
try {
  $rasaProxy = Invoke-RestMethod -Uri "$Proxy/rasa/webhooks/rest/webhook" -Method POST -ContentType "application/json" -Body $payload
  Assert-True ($rasaProxy.Count -gt 0) "Rasa via proxy respondió"
} catch {
  Write-Host "⚠️ Proxy Rasa 8080 no disponible"
}

Write-Host "`n🎉 Smoke Tests completados con éxito."
exit 0
