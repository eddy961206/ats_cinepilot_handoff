param(
    [int]$ShadowSteps = 12,
    [int]$ActiveSteps = 140,
    [int]$ActiveCountdownSeconds = 3,
    [switch]$ShadowOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$cli = Join-Path $repoRoot ".venv\Scripts\ats-cinepilot.exe"
$shadowSummaryScript = Join-Path $repoRoot "scripts\summarize_shadow_log.py"
$cvSummaryScript = Join-Path $repoRoot "scripts\summarize_cv_observer_log.py"
$logPath = Join-Path $repoRoot "data\logs\demo_active_dense_corridor_with_cv.jsonl"
$cvSummaryPath = Join-Path $repoRoot "data\logs\demo_active_dense_corridor_with_cv.cv.jsonl"
$artifactDir = Join-Path $repoRoot "data\artifacts\cv\demo_active_dense_corridor"
$runtimeContractPath = Join-Path $repoRoot "data\runtime\demo_dense_curated_corridor.runtime.yaml"
$runtimeGraphPath = Join-Path $repoRoot "data\maps\cache\demo_dense_curated_corridor.runtime.json"

Write-Host "Emergency stop:"
Write-Host "  1. Press Ctrl+C in this terminal."
Write-Host "  2. Or run scripts\demo_override_on.ps1 in another terminal."
Write-Host "  3. Or pause ATS immediately."
Write-Host "  4. Hybrid demo requires the ATS window to stay focused during active control."

& (Join-Path $repoRoot "scripts\demo_override_off.ps1")

if (Test-Path $logPath) {
    Remove-Item $logPath -Force
}
if (Test-Path $cvSummaryPath) {
    Remove-Item $cvSummaryPath -Force
}
if (Test-Path $artifactDir) {
    Remove-Item $artifactDir -Recurse -Force
}

& $python scripts\download_cv_models.py --config configs\demo_active_dense_corridor_with_cv.yaml
& $python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor_with_cv.yaml --frames 3 --require-ready
& $python scripts\ensure_demo_stop.py --config configs\demo_active_dense_corridor_with_cv.yaml --target-speed-mps 0.20
& $python scripts\fit_demo_dense_corridor.py `
    --config configs\demo_active_dense_corridor_with_cv.yaml `
    --contract configs\corridors\demo_dense_curated_corridor.yaml `
    --output-contract $runtimeContractPath `
    --output-graph $runtimeGraphPath
& $python scripts\export_demo_dense_corridor.py --contract $runtimeContractPath --output $runtimeGraphPath
& $cli check-config --config configs\demo_active_dense_corridor_with_cv.yaml --config $runtimeContractPath
& $python scripts\inspect_telemetry.py --config configs\demo_active_dense_corridor_with_cv.yaml --config $runtimeContractPath --frames 3 --require-ready
& $python scripts\inspect_controls.py --config configs\demo_active_dense_corridor_with_cv.yaml --config $runtimeContractPath --dry-run --require-ready

Write-Host "shadow qualification: $ShadowSteps steps"
& $cli run --config configs\demo_active_dense_corridor_with_cv.yaml --config $runtimeContractPath --mode shadow --steps $ShadowSteps

if ($ShadowOnly) {
    Write-Host "shadow-only requested; stopping before active demo"
    if (Test-Path $logPath) {
        & $python $shadowSummaryScript --input $logPath
    }
    if (Test-Path $cvSummaryPath) {
        & $python $cvSummaryScript --input $cvSummaryPath
    }
    exit 0
}

& $python scripts\ensure_demo_stop.py --config configs\demo_active_dense_corridor_with_cv.yaml --config $runtimeContractPath --target-speed-mps 0.20

for ($remaining = $ActiveCountdownSeconds; $remaining -gt 0; $remaining--) {
    Write-Host "dense curated CV active demo starts in $remaining s - keep the ATS window focused"
    Start-Sleep -Seconds 1
}

Write-Host "active demo: $ActiveSteps steps"
& $cli run --config configs\demo_active_dense_corridor_with_cv.yaml --config $runtimeContractPath --mode active --steps $ActiveSteps

if (Test-Path $logPath) {
    & $python $shadowSummaryScript --input $logPath
}
if (Test-Path $cvSummaryPath) {
    & $python $cvSummaryScript --input $cvSummaryPath
}

Write-Host "CV artifacts:"
Write-Host "  summary: $cvSummaryPath"
Write-Host "  artifact dir: $artifactDir"
