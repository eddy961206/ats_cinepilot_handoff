param(
    [int]$ShadowSteps = 40,
    [int]$ActiveSteps = 120,
    [int]$ActiveCountdownSeconds = 5,
    [switch]$ShadowOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$cli = Join-Path $repoRoot ".venv\Scripts\ats-cinepilot.exe"

Write-Host "Emergency stop:"
Write-Host "  1. Press Ctrl+C in this terminal."
Write-Host "  2. Or run scripts\demo_override_on.ps1 in another terminal."
Write-Host "  3. Or pause ATS immediately."
Write-Host "  4. Keyboard demo path requires the ATS window to stay focused during active control."

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

for ($remaining = $ActiveCountdownSeconds; $remaining -gt 0; $remaining--) {
    Write-Host "active demo starts in $remaining s - click the ATS window now"
    Start-Sleep -Seconds 1
}

Write-Host "active demo: $ActiveSteps steps"
& $cli run --config configs\demo_active_corridor.yaml --mode active --steps $ActiveSteps
