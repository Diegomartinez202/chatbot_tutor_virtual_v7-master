Param(
  [ValidateSet('dev','prod','vanilla')]
  [string]$Profile = 'dev',

  [ValidateSet('up','down','logs','rebuild')]
  [string]$Cmd = 'up',

  [string]$Service = ''
)

# Mapea perfiles amigables -> perfiles de docker compose
switch ($Profile) {
  'dev'     { $composeProfile = 'build' }
  'prod'    { $composeProfile = 'prod'  }
  'vanilla' { $composeProfile = 'vanilla' }
}

function Run($command) {
  Write-Host ">> $command" -ForegroundColor Cyan
  iex $command
}

# Asegura que la red externa exista (silencioso si ya existe)
try {
  docker network inspect tutorbot-local_app-net *> $null
} catch {
  Write-Host "Creando red externa tutorbot-local_app-net..." -ForegroundColor DarkYellow
  docker network create tutorbot-local_app-net | Out-Null
}

switch ($Cmd) {
  'up' {
    $cmd = "docker compose --profile $composeProfile up -d --build"
    Run $cmd
  }
  'down' {
    $cmd = "docker compose --profile $composeProfile down"
    Run $cmd
  }
  'logs' {
    if ($Service) {
      $cmd = "docker compose logs -f $Service"
    } else {
      $cmd = "docker compose --profile $composeProfile logs -f"
    }
    Run $cmd
  }
  'rebuild' {
    # Rebuild limpio + up
    $cmd1 = "docker compose --profile $composeProfile build --no-cache"
    $cmd2 = "docker compose --profile $composeProfile up -d"
    Run $cmd1
    Run $cmd2
  }
}
