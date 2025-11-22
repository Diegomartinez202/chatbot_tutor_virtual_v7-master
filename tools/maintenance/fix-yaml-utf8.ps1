# fix-yaml-utf8.ps1
# Normaliza todos los .yml/.yaml bajo rasa/data a UTF-8 (sin BOM) y fin de línea LF

param(
  [string]$Root = (Resolve-Path .),
  [string]$RelPath = "rasa\data",
  [switch]$Backup  # Si lo pasas, crea *.bak por cada archivo modificado
)

$ErrorActionPreference = "Stop"

$Target = Join-Path $Root $RelPath
Write-Host "Normalizando YAML en: $Target"

function Decode-Bytes {
  param([byte[]]$Bytes)

  # Quita BOM UTF-8 si existe
  if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
    $Bytes = $Bytes[3..($Bytes.Length-1)]
  }

  # Intenta en este orden: UTF8 estricto (sin BOM), UTF8 con BOM, ISO-8859-1, Windows-1252
  $encs = @(
    [System.Text.UTF8Encoding]::new($false, $true),
    [System.Text.UTF8Encoding]::new($true,  $true),
    [System.Text.Encoding]::GetEncoding(28591),
    [System.Text.Encoding]::GetEncoding(1252)
  )

  foreach ($e in $encs) {
    try {
      return ,($e.GetString($Bytes), $Bytes)
    } catch {
      continue
    }
  }

  # Último recurso: latin1 sin lanzar excepción
  $e = [System.Text.Encoding]::GetEncoding(28591)
  return ,($e.GetString($Bytes), $Bytes)
}

$files = Get-ChildItem -Path $Target -Recurse -Include *.yml,*.yaml -File -ErrorAction SilentlyContinue
if (-not $files -or $files.Count -eq 0) {
  Write-Host "No se encontraron .yml/.yaml bajo $Target"
  exit 0
}

$changed = 0
foreach ($f in $files) {
  $path = $f.FullName
  $origBytes = [System.IO.File]::ReadAllBytes($path)

  $result = Decode-Bytes -Bytes $origBytes
  $text = $result[0]

  # Normaliza fin de línea: CRLF/CR -> LF
  $normalized = $text -replace "`r`n", "`n" -replace "`r", "`n"

  # Reescribe como UTF-8 sin BOM
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  $newBytes = $utf8NoBom.GetBytes($normalized)

  # ¿Cambió?
  $different = $false
  if ($newBytes.Length -ne $origBytes.Length) {
    $different = $true
  } else {
    for ($i = 0; $i -lt $origBytes.Length; $i++) {
      if ($origBytes[$i] -ne $newBytes[$i]) { $different = $true; break }
    }
  }

  if ($different) {
    if ($Backup.IsPresent) {
      Copy-Item -Path $path -Destination ($path + ".bak") -Force
    }
    [System.IO.File]::WriteAllBytes($path, $newBytes)
    Write-Host ("OK  Normalizado: {0}" -f $path) -ForegroundColor Green
    $changed++
  } else {
    Write-Host ("--  Sin cambios: {0}" -f $path) -ForegroundColor DarkGray
  }
}

Write-Host ("Archivos actualizados: {0}" -f $changed) -ForegroundColor Cyan