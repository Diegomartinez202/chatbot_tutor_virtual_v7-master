<#  make.ps1
    Utilidades locales para:
      • Tareas de desarrollo (backend, frontend, tests, entrenamiento)
      • Docker Compose con perfiles (build / prod / vanilla)
      • Health/CSP checks (check-embed)
      • Helpers varios (prune, ps, logs)
    Uso:
      .\make.ps1 help
      .\make.ps1 <comando> [-Profile build|prod|vanilla] [otras opciones]
#>

[CmdletBinding(DefaultParameterSetName='main')]
param(
  [Parameter(Position=0)]
  [ValidateSet(
    # ---- help
    'help',

    # ---- Dev tasks (equivalentes a tu Makefile)
    'create-env-backend','check-embed','dev-backend','dev-frontend',
    'train','test','logs','users','upload','all-tests',

    # ---- Docker profiles
    'up-build','down-build','logs-build',
    'up-prod','down-prod','logs-prod',
    'up-vanilla','down-vanilla','logs-vanilla',

    # ---- Docker utils
    'ps','rebuild','prune','restart-backend','reload-nginx'
  )]
  [string]$Command = 'help',

  [ValidateSet('build','prod','vanilla')]
  [string]$Profile = 'build',

  [int]$BACKEND_PORT = 8000,
  [int]$FRONTEND_PORT = 5173,
  [string]$BACKEND_URL = 'http://localhost:8000'
)

# =========================
# Config básica
# =========================
$script:Project   = 'tutorbot-local'
$script:RepoRoot  = (Resolve-Path -LiteralPath '.').Path
$script:Compose   = Join-Path $RepoRoot 'docker-compose.yml'
$script:BackendEnv      = Join-Path $RepoRoot 'backend\.env'
$script:BackendEnvExmp  = Join-Path $RepoRoot 'backend\.env.example'
$script:CheckEmbedSh    = Join-Path $RepoRoot 'check_embed.sh'

# =========================
# Helpers
# =========================
function Get-ComposeBase {
  if (Get-Command 'docker' -ErrorAction SilentlyContinue) {
    try {
      $v = docker compose version 2>$null
      if ($LASTEXITCODE -eq 0) { return @('docker','compose') }
    } catch {}
  }
  if (Get-Command 'docker-compose' -ErrorAction SilentlyContinue) {
    return @('docker-compose')
  }
  throw "No se encontró 'docker compose' ni 'docker-compose' en PATH."
}
$script:ComposeCmd = Get-ComposeBase

function Get-ComposeArgs([string]$profile) {
  @('-p',$script:Project,'--profile', $profile, '-f', $script:Compose)
}

function Invoke-Compose {
  param(
    [string]$Profile,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ComposeArgs
  )
  $args = @()
  $args += (Get-ComposeArgs $Profile)
  $args += $ComposeArgs
  & $script:ComposeCmd @args
  if ($LASTEXITCODE -ne 0) { throw "Comando falló: $($script:ComposeCmd -join ' ') $($args -join ' ')" }
}

function Have-Bash {
  return [bool](Get-Command bash -ErrorAction SilentlyContinue)
}

function Have-Npm {
  return [bool](Get-Command npm -ErrorAction SilentlyContinue)
}

function Have-Python {
  return [bool](Get-Command python -ErrorAction SilentlyContinue)
}

function Show-Header([string]$msg) {
  Write-Host "`n=== $msg ===" -ForegroundColor Cyan
}

# =========================
# Sección: Dev tasks (Makefile parity)
# =========================
function Invoke-CreateEnvBackend {
  Show-Header "create-env-backend"
  if (-not (Test-Path $script:BackendEnv)) {
    if (Test-Path $script:BackendEnvExmp) {
      Copy-Item $script:BackendEnvExmp $script:BackendEnv -Force
      Write-Host "✅ backend/.env creado desde backend/.env.example"
    } else {
      Write-Host "⚠️ No existe backend/.env.example, crea $script:BackendEnv manualmente." -ForegroundColor Yellow
    }
  } else {
    Write-Host "ℹ️ backend/.env ya existe. Nada que copiar."
  }
}

function Invoke-CheckEmbed {
  Show-Header "check-embed ($BACKEND_URL)"
  if (Test-Path $script:CheckEmbedSh -and (Have-Bash)) {
    & bash $script:CheckEmbedSh $BACKEND_URL
    return
  }
  # Fallback PowerShell nativo
  try {
    $health = Invoke-WebRequest -UseBasicParsing -Uri ($BACKEND_URL.TrimEnd('/') + '/health') -TimeoutSec 10
    Write-Host "Health: $($health.StatusCode)" -ForegroundColor Green
  } catch {
    Write-Host "❌ No se pudo consultar /health en $BACKEND_URL" -ForegroundColor Red
  }
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $BACKEND_URL -TimeoutSec 10
    $csp = $resp.Headers['Content-Security-Policy']
    if ($csp) {
      Write-Host "CSP: $csp"
    } else {
      Write-Host "ℹ️ Sin CSP en raíz (ok si sólo se aplica en rutas específicas)."
    }
  } catch {
    Write-Host "⚠️ No se pudo leer CSP de $BACKEND_URL" -ForegroundColor Yellow
  }
}

function Invoke-DevBackend {
  Show-Header "dev-backend (uvicorn, port $BACKEND_PORT)"
  if (-not (Have-Python)) { throw "Python no encontrado en PATH." }
  & python -m uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
}

function Invoke-DevFrontend {
  Show-Header "dev-frontend (Vite, port $FRONTEND_PORT)"
  if (-not (Have-Npm)) { throw "npm no encontrado en PATH." }
  $frontendDir1 = Join-Path $script:RepoRoot 'frontend'
  $frontendDir2 = Join-Path $script:RepoRoot 'admin_panel_react'
  $dir = if (Test-Path $frontendDir1) { $frontendDir1 } elseif (Test-Path $frontendDir2) { $frontendDir2 } else { $null }
  if (-not $dir) { throw "No se encontró carpeta 'frontend' ni 'admin_panel_react'." }
  Push-Location $dir
  try {
    npm run dev -- --host --port $FRONTEND_PORT
  } finally {
    Pop-Location
  }
}

function Invoke-Train {
  Show-Header "train (Rasa)"
  $trainSh = Join-Path $script:RepoRoot 'train_rasa.sh'
  if ((Test-Path $trainSh) -and (Have-Bash)) {
    & bash $trainSh
  } elseif (Get-Command rasa -ErrorAction SilentlyContinue) {
    & rasa train
  } else {
    throw "No hay bash+train_rasa.sh ni 'rasa' en PATH."
  }
}

function Invoke-Pytest([string]$pattern) {
  if (-not (Have-Python)) { throw "Python no encontrado en PATH." }
  $args = @('backend/test')
  if ($pattern) { $args = @("backend/test/$pattern") }
  & python -m pytest @args --disable-warnings
}

function Invoke-Test        { Show-Header "test";  Invoke-Pytest "" }
function Invoke-TestLogs    { Show-Header "logs";  Invoke-Pytest "test_logs.py" }
function Invoke-TestUsers   { Show-Header "users"; Invoke-Pytest "test_users.py" }
function Invoke-TestUpload  { Show-Header "upload";Invoke-Pytest "test_upload_csv.py" }
function Invoke-AllTests {
  Show-Header "all-tests"
  $scriptAll = Join-Path $script:RepoRoot 'test_all.sh'
  if ((Test-Path $scriptAll) -and (Have-Bash)) {
    & bash $scriptAll
  } else {
    Write-Host "⚠️ test_all.sh no encontrado. Corriendo suite por defecto (pytest backend/test)" -ForegroundColor Yellow
    Invoke-Test
  }
}

# =========================
# Sección: Docker (perfiles)
# =========================
function Invoke-UpBuild    { Invoke-Compose -Profile build up -d --build }
function Invoke-DownBuild  { Invoke-Compose -Profile build down }
function Invoke-LogsBuild  { Invoke-Compose -Profile build logs -f }

function Invoke-UpProd     { Invoke-Compose -Profile prod  up -d --build }
function Invoke-DownProd   { Invoke-Compose -Profile prod  down }
function Invoke-LogsProd   { Invoke-Compose -Profile prod  logs -f }

function Invoke-UpVanilla  { Invoke-Compose -Profile vanilla up -d --build }
function Invoke-DownVanilla{ Invoke-Compose -Profile vanilla down }
function Invoke-LogsVanilla{ Invoke-Compose -Profile vanilla logs -f }

# utilidades
function Invoke-Ps         { & $script:ComposeCmd @('-p',$script:Project,'ps') }
function Invoke-Prune      { docker system prune -f; docker volume prune -f }

function Invoke-Rebuild {
  switch ($Profile) {
    'build'   { Invoke-UpBuild }
    'prod'    { Invoke-UpProd }
    'vanilla' { Invoke-UpVanilla }
    default   { throw "Perfil desconocido: $Profile" }
  }
}

function Invoke-RestartBackend {
  switch ($Profile) {
    'build'   { Invoke-Compose -Profile build restart backend-dev }
    'prod'    { Invoke-Compose -Profile prod  restart backend }
    default   { throw "restart-backend solo soporta build o prod (actual: $Profile)" }
  }
}

function Invoke-ReloadNginx {
  try { docker exec -it nginx nginx -s reload | Out-Null } catch {}
  try { docker exec -it nginx-dev nginx -s reload | Out-Null } catch {}
  Write-Host "Nginx reload solicitado (prod y build, si existen)."
}

# =========================
# Ayuda
# =========================
function Show-Help {
@"
Comandos disponibles:

  # ==== Dev (equivalentes Makefile) ====
  create-env-backend         Copia backend/.env.example → backend/.env (si no existe)
  check-embed                Verifica /health y cabeceras CSP en BACKEND_URL (actual: $BACKEND_URL)
  dev-backend                uvicorn backend.main:app --reload (puerto $BACKEND_PORT)
  dev-frontend               Vite dev server (puerto $FRONTEND_PORT)
  train                      Entrena Rasa (train_rasa.sh o 'rasa train')
  test                       pytest backend/test
  logs                       pytest backend/test/test_logs.py
  users                      pytest backend/test/test_users.py
  upload                     pytest backend/test/test_upload_csv.py
  all-tests                  test_all.sh si existe; si no, pytest backend/test

  # ==== Docker (perfiles) ====
  up-build / down-build / logs-build
  up-prod  / down-prod  / logs-prod
  up-vanilla / down-vanilla / logs-vanilla

  # ==== Utilidades ====
  ps                         Estado de contenedores
  rebuild [-Profile ...]     Reconstruye y levanta según perfil (build|prod|vanilla)
  prune                      Limpia recursos Docker
  restart-backend            Reinicia backend-dev (build) o backend (prod)
  reload-nginx               Recarga Nginx (si corre)

Ejemplos:
  .\make.ps1 create-env-backend
  .\make.ps1 check-embed -BACKEND_URL http://localhost:8000
  .\make.ps1 dev-backend -BACKEND_PORT 8001
  .\make.ps1 up-build
  .\make.ps1 restart-backend -Profile prod
"@ | Write-Host
}

# =========================
# Dispatcher
# =========================
switch ($Command) {
  'help'               { Show-Help }

  # Dev / Makefile parity
  'create-env-backend' { Invoke-CreateEnvBackend }
  'check-embed'        { Invoke-CheckEmbed }
  'dev-backend'        { Invoke-DevBackend }
  'dev-frontend'       { Invoke-DevFrontend }
  'train'              { Invoke-Train }
  'test'               { Invoke-Test }
  'logs'               { Invoke-TestLogs }
  'users'              { Invoke-TestUsers }
  'upload'             { Invoke-TestUpload }
  'all-tests'          { Invoke-AllTests }

  # Docker profiles
  'up-build'           { Invoke-UpBuild }
  'down-build'         { Invoke-DownBuild }
  'logs-build'         { Invoke-LogsBuild }

  'up-prod'            { Invoke-UpProd }
  'down-prod'          { Invoke-DownProd }
  'logs-prod'          { Invoke-LogsProd }

  'up-vanilla'         { Invoke-UpVanilla }
  'down-vanilla'       { Invoke-DownVanilla }
  'logs-vanilla'       { Invoke-LogsVanilla }

  # Utils
  'ps'                 { Invoke-Ps }
  'rebuild'            { Invoke-Rebuild }
  'prune'              { Invoke-Prune }
  'restart-backend'    { Invoke-RestartBackend }
  'reload-nginx'       { Invoke-ReloadNginx }

  default              { Show-Help }
}