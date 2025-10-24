Param(
  [string]$Root = ".",
  [string]$RoutesDir = "backend/routes",
  [string]$ControllersDir = "backend/controllers"
)

function Get-FastApiEndpoints {
  param([string]$Dir)

  $files = Get-ChildItem -Path $Dir -Recurse -Filter *.py -ErrorAction SilentlyContinue
  $endpoints = @()

  foreach ($f in $files) {
    $text = Get-Content -Raw -Path $f.FullName

    # 1) Mapa routerName -> prefix (si existe)
    $routerPrefixes = @{}
    $routerDeclRegex = [regex]'(?m)^\s*([A-Za-z_][\w]*)\s*=\s*APIRouter\(([^)]*)\)'
    foreach ($m in $routerDeclRegex.Matches($text)) {
      $routerName = $m.Groups[1].Value
      $args = $m.Groups[2].Value
      $prefix = ""
      $prefixMatch = [regex]::Match($args, 'prefix\s*=\s*["'']([^"'']+)["'']')
      if ($prefixMatch.Success) { $prefix = $prefixMatch.Groups[1].Value }
      $routerPrefixes[$routerName] = $prefix
    }

    # 2) Extraer decoradores @<router>.<method>("<path>")
    $decRegex = [regex]'(?m)^\s*@\s*([A-Za-z_][\w]*)\.(get|post|put|delete|patch|options|head)\(\s*["'']([^"'']+)["'']'
    foreach ($m in $decRegex.Matches($text)) {
      $routerName = $m.Groups[1].Value
      $method = $m.Groups[2].Value.ToUpper()
      $path = $m.Groups[3].Value

      $prefix = ""
      if ($routerPrefixes.ContainsKey($routerName)) { $prefix = $routerPrefixes[$routerName] }

      # 3) Componer ruta completa con prefix si existe
      $fullPath = if ($prefix) { "$prefix/$path" } else { $path }

      # Normalizar // y quitar trailing /
      $fullPath = $fullPath -replace '//+', '/'
      if ($fullPath.Length -gt 1 -and $fullPath.EndsWith('/')) {
        $fullPath = $fullPath.TrimEnd('/')
      }

      $endpoints += [pscustomobject]@{
        File   = $f.FullName
        Router = $routerName
        Method = $method
        Path   = $fullPath
        Dir    = $Dir
        Key    = "$method $fullPath"
      }
    }
  }

  return $endpoints
}

$routes = Get-FastApiEndpoints -Dir (Join-Path $Root $RoutesDir)
$controllers = Get-FastApiEndpoints -Dir (Join-Path $Root $ControllersDir)

# Unir y detectar conflictos (misma Method+Path presentes en ambos orígenes)
$byKey = @{}
foreach ($e in $routes + $controllers) {
  if (-not $byKey.ContainsKey($e.Key)) { $byKey[$e.Key] = @() }
  $byKey[$e.Key] += $e
}

$conflicts = $byKey.GetEnumerator() | Where-Object {
  ($_.Value | Select-Object -ExpandProperty Dir | Select-Object -Unique).Count -gt 1
} | ForEach-Object {
  $_.Value
} | Sort-Object Path, Method, Dir

if ($conflicts.Count -eq 0) {
  Write-Host "✅ No se detectaron conflictos de endpoints entre '$RoutesDir' y '$ControllersDir'."
} else {
  Write-Host "⚠️ Conflictos detectados (mismo Method + Path en ambos árboles):`n" -ForegroundColor Yellow
  $conflicts | Format-Table Method, Path, Dir, File -AutoSize
  "`nSugerencias:"
  "- Revisa el orden de app.include_router(...)"
  "- Considera deshabilitar el legacy que duplique rutas (p. ej. INTENT legacy)."
  "- Unifica rutas repetidas en un solo router."
}