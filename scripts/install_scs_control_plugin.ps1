param(
    [string]$ExternalRepoPath = "",
    [string]$AtsGameDir = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$workspaceRoot = Split-Path $repoRoot -Parent
if ([string]::IsNullOrWhiteSpace($ExternalRepoPath)) {
    $ExternalRepoPath = Join-Path $workspaceRoot "_ext\\scs-sdk-controller"
}

$vsDevCmd = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
$cmakeExe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"

if (-not (Test-Path $ExternalRepoPath)) {
    gh repo clone ETS2LA/scs-sdk-controller $ExternalRepoPath
}
if (-not (Test-Path $vsDevCmd)) {
    throw "Build Tools not found: $vsDevCmd"
}
if (-not (Test-Path $cmakeExe)) {
    throw "CMake not found: $cmakeExe"
}

if ([string]::IsNullOrWhiteSpace($AtsGameDir)) {
    $AtsGameDir = & ".\.venv\Scripts\python.exe" -c "from ats_cinepilot.bridge.live_diagnostics import find_ats_game_dir; path=find_ats_game_dir(); print(path if path else '')"
}
if ([string]::IsNullOrWhiteSpace($AtsGameDir) -or -not (Test-Path $AtsGameDir)) {
    throw "ATS game directory not found."
}

$buildDir = Join-Path $ExternalRepoPath "build"
$dllPath = Join-Path $buildDir "Release\scs_sdk_controller.dll"
$pluginDir = Join-Path $AtsGameDir "bin\win_x64\plugins"
$pluginTarget = Join-Path $pluginDir "scs_sdk_controller.dll"

& ".\.venv\Scripts\python.exe" "scripts\patch_scs_control_plugin.py" --repo $ExternalRepoPath

cmd /c "`"$vsDevCmd`" -arch=x64 -host_arch=x64 >nul && `"$cmakeExe`" -S `"$ExternalRepoPath`" -B `"$buildDir`" && `"$cmakeExe`" --build `"$buildDir`" --config Release"

if (-not (Test-Path $dllPath)) {
    throw "Build completed without DLL output: $dllPath"
}

New-Item -ItemType Directory -Path $pluginDir -Force | Out-Null
Copy-Item $dllPath $pluginTarget -Force

Write-Host "installed control DLL: $pluginTarget"
Write-Host "python module path: $ExternalRepoPath"
