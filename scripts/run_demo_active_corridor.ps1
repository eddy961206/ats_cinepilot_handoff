param(
    [int]$ShadowSteps = 40,
    [int]$ActiveSteps = 120,
    [switch]$ShadowOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$cli = Join-Path $repoRoot ".venv\Scripts\ats-cinepilot.exe"
$controlModulePath = (Resolve-Path (Join-Path $repoRoot "..\_ext\scs-sdk-controller")).Path
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$controlModulePath;$env:PYTHONPATH" } else { $controlModulePath }

Write-Host "Emergency stop:"
Write-Host "  1. Press Ctrl+C in this terminal."
Write-Host "  2. Or run scripts\demo_override_on.ps1 in another terminal."
Write-Host "  3. Or pause ATS immediately."

& (Join-Path $repoRoot "scripts\demo_override_off.ps1")

& $cli check-config --config configs\demo_active_corridor.yaml
& $python scripts\inspect_telemetry.py --config configs\demo_active_corridor.yaml --frames 3 --require-ready
& $python scripts\inspect_controls.py --config configs\demo_active_corridor.yaml --dry-run --require-ready

Write-Host "shadow qualification: $ShadowSteps steps"
& $cli run --config configs\demo_active_corridor.yaml --mode shadow --steps $ShadowSteps

if ($ShadowOnly) {
    Write-Host "shadow-only requested; stopping before active demo"
    exit 0
}

Write-Host "active demo: $ActiveSteps steps"
& $cli run --config configs\demo_active_corridor.yaml --mode active --steps $ActiveSteps
