# docs/DOCKER.md (opcional)

```md
# 🐳 Operación Docker – Cheatsheet

## Build y run por perfil
```bash
docker compose --profile build up -d --build
docker compose --profile prod  up -d --build
docker compose --profile vanilla up -d
Logs y estado
bash
Copiar código
docker compose ps
docker compose logs -f backend
docker compose logs -f rasa action-server nginx
Entrar a contenedores
bash
Copiar código
docker exec -it backend sh
docker exec -it rasa sh
docker exec -it action-server sh
Limpiar (con cuidado)
bash
Copiar código
docker compose down
docker system prune -f
docker volume ls
docker volume rm <volumen>
Tags/CI (ejemplo)
bash
Copiar código
docker build -t org/admin:latest ./admin_panel_react
docker push org/admin:latest
php
Copiar código

---

# scripts/tasks.ps1 (atajos “one-click”)

```powershell
param(
  [ValidateSet("build","prod","vanilla")]
  [string]$Profile = "build",
  [switch]$Rebuild,
  [switch]$Down,
  [switch]$Logs,
  [switch]$Health
)

$ErrorActionPreference = "Stop"

function Banner($txt){ Write-Host "`n=== $txt ===" -ForegroundColor Cyan }

if ($Down) {
  Banner "Compose DOWN ($Profile)"
  docker compose --profile $Profile down
  exit 0
}

if ($Rebuild) {
  Banner "Compose UP --build ($Profile)"
  docker compose --profile $Profile up -d --build
} else {
  Banner "Compose UP ($Profile)"
  docker compose --profile $Profile up -d
}

if ($Logs) {
  Banner "Tail logs ($Profile)"
  docker compose --profile $Profile logs -f
}

if ($Health) {
  Banner "Health check"
  $fast = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://127.0.0.1:8000/chat/health" -ErrorAction SilentlyContinue
  $rasa = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://127.0.0.1:5005/status" -ErrorAction SilentlyContinue
  $acts = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://127.0.0.1:5055/health" -ErrorAction SilentlyContinue
  if ($fast.StatusCode -eq 200 -and $rasa.StatusCode -eq 200 -and $acts.StatusCode -eq 200) {
    Write-Host "OK: FastAPI, Rasa, Actions" -ForegroundColor Green
  } else {
    Write-Host "Algún servicio falló" -ForegroundColor Yellow
  }
}