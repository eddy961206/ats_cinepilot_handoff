$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$flagPath = Join-Path $repoRoot "data\runtime\demo_override.flag"
New-Item -ItemType Directory -Path (Split-Path $flagPath -Parent) -Force | Out-Null
New-Item -ItemType File -Path $flagPath -Force | Out-Null
Write-Host "demo override enabled: $flagPath"
