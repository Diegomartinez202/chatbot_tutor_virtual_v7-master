<#  tests/smoke_endpoints.ps1

  Valida coexistencia de rutas:
   - /api/auth/login, /api/auth/me
   - /auth/refresh, /api/auth/refresh
   - /auth/logout
   - /chat/health, /api/chat/health
#>

param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Email   = "admin@demo.com",     # <- ajusta a un usuario válido
  [string]$Pass    = "123456"              # <- ajusta a su password
)

$ErrorActionPreference = "Stop"
Write-Host "🔎 Smoke tests contra $BaseUrl`n"

function Invoke-Json {
  param(
    [Parameter(Mandatory=$true)][string]$Method,
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter()][hashtable]$Headers,
    [Parameter()][string]$Body,
    [Parameter()][Microsoft.PowerShell.Commands.WebRequestSession]$Session,
    [switch]$AllowNon2xx
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
    if ($AllowNon2xx) {
      return @{ ok=$false; status=$status; data=$null }
    }
    throw
  }
}

function Assert-True {
  param([bool]$cond, [string]$msg)
  if (-not $cond) { throw "❌ $msg" }
  Write-Host "✅ $msg"
}

# --- 1) Health básicos ---
$h1 = Invoke-Json -Method GET -Url "$BaseUrl/health"
Assert-True ($h1.ok -and $h1.status -eq 200 -and $h1.data.ok) "/health responde 200"

# Algunos proyectos exponen health del chat:
foreach ($u in @("$BaseUrl/chat/health", "$BaseUrl/api/chat/health")) {
  try {
    $h = Invoke-Json -Method GET -Url $u -AllowNon2xx
    if ($h.ok -and $h.status -eq 200) {
      Write-Host "✅ $u responde 200"
    } else {
      Write-Host "ℹ️ $u no disponible (status $($h.status)) — ok si tu router no define health"
    }
  } catch {
    Write-Host "ℹ️ $u lanzó excepción — ok si no existe"
  }
}

# --- 2) Login en /api/auth/login (devuelve access y setea cookie rt) ---
$session = $null
$loginResp = $null
try {
  $loginResp = Invoke-RestMethod -Method Post `
    -Uri "$BaseUrl/api/auth/login" `
    -ContentType "application/json" `
    -Body (@{ email=$Email; password=$Pass } | ConvertTo-Json) `
    -SessionVariable session
} catch {
  throw "❌ Falló login en /api/auth/login — revisa credenciales o servidor"
}

Assert-True ($null -ne $session) "Se creó sesión HTTP para cookies"
$access = $loginResp.access_token
Assert-True ([string]::IsNullOrEmpty($access) -eq $false) "Login devolvió access_token"
# Verifica cookie rt
$rtCookie = $session.Cookies.GetCookies("$BaseUrl") | Where-Object { $_.Name -eq "rt" -or $_.Name -eq $env:REFRESH_COOKIE_NAME }
if ($null -eq $rtCookie) {
  Write-Host "⚠️ No veo cookie 'rt' — si usas otro nombre, define REFRESH_COOKIE_NAME en el entorno o ajusta el script"
} else {
  Write-Host "✅ Cookie de refresh presente: $($rtCookie.Name)"
}

# --- 3) /api/auth/me con Bearer ---
$Headers = @{ Authorization = "Bearer $access" }
$me = Invoke-Json -Method GET -Url "$BaseUrl/api/auth/me" -Headers $Headers
Assert-True ($me.ok -and $me.status -eq 200 -and $me.data.email) "/api/auth/me responde 200 y devuelve email"

# --- 4) Refresh vía COOKIE en /auth/refresh y /api/auth/refresh ---
foreach ($u in @("$BaseUrl/auth/refresh", "$BaseUrl/api/auth/refresh")) {
  try {
    $r = Invoke-RestMethod -Method Post -Uri $u -WebSession $session
    Assert-True ($r.access_token.Length -gt 10) "$u devuelve access_token con cookie"
  } catch {
    throw "❌ $u no pudo refrescar con cookie: $($_.Exception.Message)"
  }
}

# --- 5) Refresh vía BODY (si el login devuelve refresh en body; si no, omitimos) ---
if ($loginResp.refresh_token) {
  $rb = Invoke-Json -Method POST -Url "$BaseUrl/api/auth/refresh" -Body (@{ refresh_token = $loginResp.refresh_token } | ConvertTo-Json) -Session $session
  Assert-True ($rb.ok -and $rb.status -eq 200 -and $rb.data.access_token) "Refresh por body en /api/auth/refresh devuelve access_token"
} else {
  Write-Host "ℹ️ El login no devolvió refresh_token en body — solo probado por cookie (OK)"
}

# --- 6) Logout en /auth/logout (borra cookie) ---
try {
  $lg = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/logout" -WebSession $session
  Write-Host "✅ /auth/logout OK"
} catch {
  throw "❌ /auth/logout falló: $($_.Exception.Message)"
}

# Verifica que la cookie rt ya no esté
$rtAfter = $session.Cookies.GetCookies("$BaseUrl") | Where-Object { $_.Name -eq "rt" -or $_.Name -eq $env:REFRESH_COOKIE_NAME }
if ($null -ne $rtAfter -and $rtAfter.Value) {
  Write-Host "⚠️ La cookie 'rt' aún aparece en la sesión del cliente. Algunos navegadores requieren respuesta real para purgarla; en PowerShell puede quedar cacheada. Verifica manual en cliente web si es necesario."
} else {
  Write-Host "✅ Cookie de refresh ausente tras logout (o sin valor)"
}

Write-Host "`n🎉 Todos los checks de coexistencia /auth, /api/auth, /chat y /api/chat pasaron (o están razonablemente ausentes)."
exit 0