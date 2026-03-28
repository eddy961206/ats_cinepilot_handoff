$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$flagPath = Join-Path $repoRoot "data\runtime\demo_override.flag"
if (Test-Path $flagPath) {
    Remove-Item $flagPath -Force
}
Write-Host "demo override cleared: $flagPath"
