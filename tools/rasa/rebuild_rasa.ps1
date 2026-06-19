Param(
  [ValidateSet('build','prod','vanilla')]
  [string]$Profile = 'build',
  [switch]$NoCache,
  [switch]$Recreate
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

function Banner([string]$Text) {
  Write-Host ""
  Write-Host "==== $Text ====" -ForegroundColor Cyan
}

function Run([string]$Exe, [string[]]$ArgList) {
  Write-Host (">> " + $Exe + " " + ($ArgList -join " ")) -ForegroundColor DarkGray
  & $Exe @ArgList
  if ($LASTEXITCODE -ne 0) { throw "Error ejecutando: $Exe $($ArgList -join ' ')" }
}

# 1) Down limpio
Banner "Bajando stack (remove-orphans)"
Run "docker" @("compose","down","--remove-orphans")
if ($Recreate) {
  Banner "Prune (opcional por --Recreate)"
  Run "docker" @("system","prune","-f")
}

# 2) Build imágenes
Banner "Build de imagenes"
$buildArgList = @("compose","build","rasa","action-server")
if ($NoCache) { $buildArgList += "--no-cache" }
Run "docker" $buildArgList

# 3) Subir con el perfil elegido
Banner "Levantando stack con perfil: $Profile"
Run "docker" @("compose","--profile",$Profile,"up","-d")

Start-Sleep -Seconds 5

# 4) Healthchecks rápidos
Banner "Comprobando health Rasa y Action Server"
$okRasa = $false
$okActions = $false
for ($i=0; $i -lt 15; $i++) {
  try {
    $r1 = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:5005/status" -TimeoutSec 3
    if ($r1.StatusCode -eq 200) { $okRasa = $true }
  } catch {}
  try {
    $r2 = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:5055/health" -TimeoutSec 3
    if ($r2.StatusCode -eq 200) { $okActions = $true }
  } catch {}
  if ($okRasa -and $okActions) { break }
  Start-Sleep -Seconds 3
}
if (-not $okRasa)   { Write-Host "Aviso: Rasa aún no responde /status" -ForegroundColor Yellow }
if (-not $okActions){ Write-Host "Aviso: Action Server aún no responde /health" -ForegroundColor Yellow }

# 5) Validación
Banner "Validando domain + data"
Run "docker" @("compose","exec","rasa","rasa","data","validate","--domain","/app/domain.yml","--data","/app/data")

# 6) Entrenamiento
Banner "Entrenando modelo"
Run "docker" @("compose","exec","rasa","rasa","train")

# 7) Reinicio de Rasa
Banner "Reiniciando Rasa"
Run "docker" @("compose","restart","rasa")
Start-Sleep -Seconds 8

# 8) Estado final
Banner "Estado final"
try {
  $status = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:5005/status" -TimeoutSec 5
  $json = $status.Content | ConvertFrom-Json
  Write-Host ("Modelo: {0} | Trabajos activos: {1}" -f $json.model_id, $json.num_active_training_jobs) -ForegroundColor Green
} catch {
  Write-Host "No pude leer /status de Rasa" -ForegroundColor Yellow
}

Run "docker" @("compose","ps")