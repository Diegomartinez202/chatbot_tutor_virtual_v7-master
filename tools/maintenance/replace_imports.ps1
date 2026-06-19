param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('utils','models','services','schemas','all')]
  [string]$Area,
  [switch]$Apply,   # si no lo pones, solo muestra (preview)
  [switch]$Clean    # elimina líneas exactamente duplicadas "from backend.<area> import ..."
)

$ErrorActionPreference = 'Stop'

function Get-Files {
  Get-ChildItem .\backend -Recurse -Filter *.py |
    Where-Object {
      $_.FullName -notmatch '\\(__pycache__|\.venv|venv|env|node_modules|dist|build)\\'
    }
}

$patternMap = @{
  "utils"    = 'from\s+backend\.utils\.\w+\s+import\s+'
  "models"   = 'from\s+backend\.models\.\w+\s+import\s+'
  "services" = 'from\s+backend\.services\.\w+\s+import\s+'
  "schemas"  = 'from\s+backend\.schemas\.\w+\s+import\s+'
}

function Process-Area {
  param([string]$OneArea)

  $pattern = $patternMap[$OneArea]
  $replace = "from backend.$OneArea import "
  $importLineRegex = "^\s*from\s+backend\.$OneArea\s+import\s+.+$"

  $files = Get-Files
  $changed = @()

  foreach($f in $files){
    $text = Get-Content $f.FullName -Raw -ErrorAction Stop
    $orig = $text

    # 1) Mostrar ANTES → DESPUÉS (preview)
    $matches = Select-String -InputObject $text -Pattern $pattern -AllMatches
    foreach($m in $matches){
      $before = $m.Line.Trim()
      $after  = ($m.Line -replace $pattern, $replace).Trim()
      Write-Host "`n[$OneArea] Archivo:" $f.FullName -ForegroundColor Cyan
      Write-Host "ANTES:  " $before -ForegroundColor Yellow
      Write-Host "DESPUÉS:" $after  -ForegroundColor Green
    }

    # 2) Aplicar reemplazo si -Apply
    $newText = $text
    if($Apply){
      $newText = $newText -replace $pattern, $replace
    }

    # 3) Limpiar duplicados exactos si -Clean
    if($Clean){
      $lines = $newText -split "`r?`n"
      $seen = @{}
      $out = New-Object System.Collections.Generic.List[string]
      foreach($ln in $lines){
        if($ln -match $importLineRegex){
          if(-not $seen.ContainsKey($ln)){
            $seen[$ln] = $true
            [void]$out.Add($ln)
          } else {
            # duplicado exacto → omitir
          }
        } else {
          [void]$out.Add($ln)
        }
      }
      $newText = ($out -join "`n")
      if($text.EndsWith("`n")){ $newText += "`n" }
    }

    if(($Apply -or $Clean) -and $newText -ne $orig){
      # Guardar UTF-8 sin BOM
      [System.IO.File]::WriteAllText($f.FullName, $newText, (New-Object System.Text.UTF8Encoding($false)))
      $changed += $f.FullName
    }
  }

  if($Apply -or $Clean){
    if($changed.Count){
      Write-Host "`n✅ [$OneArea] Cambios escritos en $($changed.Count) archivo(s)." -ForegroundColor Green
    } else {
      Write-Host "`nℹ️ [$OneArea] No hubo cambios que escribir." -ForegroundColor Gray
    }
  } else {
    Write-Host "`n🟡 [$OneArea] Vista previa (no se escribió nada)." -ForegroundColor Yellow
  }
}

if($Area -eq 'all'){
  foreach($a in @('utils','models','services','schemas')){ Process-Area -OneArea $a }
} else {
  Process-Area -OneArea $Area
}