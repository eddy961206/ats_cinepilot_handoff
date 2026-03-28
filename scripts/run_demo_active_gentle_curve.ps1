param(
    [int]$ShadowSteps = 25,
    [int]$ActiveSteps = 120,
    [int]$ActiveCountdownSeconds = 5,
    [switch]$ShadowOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$cli = Join-Path $repoRoot ".venv\Scripts\ats-cinepilot.exe"
$summaryScript = Join-Path $repoRoot "scripts\summarize_shadow_log.py"
$logPath = Join-Path $repoRoot "data\logs\demo_active_gentle_curve.jsonl"

Write-Host "Emergency stop:"
Write-Host "  1. Press Ctrl+C in this terminal."
Write-Host "  2. Or run scripts\demo_override_on.ps1 in another terminal."
Write-Host "  3. Or pause ATS immediately."
Write-Host "  4. Hybrid demo requires the ATS window to stay focused during active control."

& (Join-Path $repoRoot "scripts\demo_override_off.ps1")

if (Test-Path $logPath) {
    Remove-Item $logPath -Force
}

& $cli check-config --config configs\demo_active_gentle_curve.yaml
& $python scripts\inspect_telemetry.py --config configs\demo_active_gentle_curve.yaml --frames 3 --require-ready
& $python scripts\inspect_controls.py --config configs\demo_active_gentle_curve.yaml --dry-run --require-ready

Write-Host "shadow qualification: $ShadowSteps steps"
& $cli run --config configs\demo_active_gentle_curve.yaml --mode shadow --steps $ShadowSteps

if ($ShadowOnly) {
    Write-Host "shadow-only requested; stopping before active demo"
    if (Test-Path $logPath) {
        & $python $summaryScript --input $logPath
    }
    exit 0
}

for ($remaining = $ActiveCountdownSeconds; $remaining -gt 0; $remaining--) {
    Write-Host "gentle-curve active demo starts in $remaining s - click the ATS window now"
    Start-Sleep -Seconds 1
}

Write-Host "active demo: $ActiveSteps steps"
& $cli run --config configs\demo_active_gentle_curve.yaml --mode active --steps $ActiveSteps

if (Test-Path $logPath) {
    & $python $summaryScript --input $logPath
}
