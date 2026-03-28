param(
    [int]$Steps = 120
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$cli = Join-Path $repoRoot ".venv\Scripts\ats-cinepilot.exe"
$summaryScript = Join-Path $repoRoot "scripts\summarize_cv_observer_log.py"
$artifactDir = Join-Path $repoRoot "data\artifacts\cv\observer_dense_corridor"
$summaryPath = Join-Path $repoRoot "data\logs\cv_observer_dense_corridor.cv.jsonl"

Write-Host "CV observer only run."
Write-Host "ATS window does not need to stay focused because control is noop."

if (Test-Path $artifactDir) {
    Remove-Item $artifactDir -Recurse -Force
}
if (Test-Path $summaryPath) {
    Remove-Item $summaryPath -Force
}

& $python scripts\download_cv_models.py --config configs\cv_observer_dense_corridor.yaml
& $cli check-config --config configs\cv_observer_dense_corridor.yaml
& $python scripts\inspect_telemetry.py --config configs\cv_observer_dense_corridor.yaml --frames 3 --require-ready
& $cli run --config configs\cv_observer_dense_corridor.yaml --mode shadow --steps $Steps

if (Test-Path $summaryPath) {
    & $python $summaryScript --input $summaryPath
}

Write-Host "CV artifacts:"
Write-Host "  summary: $summaryPath"
Write-Host "  artifact dir: $artifactDir"
