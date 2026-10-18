# Get the Python dev environment going on the laptop's Windows side, then run
# exactly what CI runs. Safe to rerun.
#
#   powershell -ExecutionPolicy Bypass -File scripts\setup-dev.ps1
#
# The repo lives in OneDrive on the laptop, so the venv goes OUTSIDE it,
# in %USERPROFILE%\.venvs\extra-15pc-gum. Otherwise OneDrive tries to sync
# thousands of package files.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $env:USERPROFILE ".venvs\extra-15pc-gum"
$py = Join-Path $venv "Scripts\python.exe"

Set-Location $repo

Write-Host "==> Python venv at $venv"
if (-not (Test-Path $py)) { python -m venv $venv }
& $py -m pip install -q --upgrade pip
& $py -m pip install -q --group dev -e .
Write-Host "    $(& $py --version)"

Write-Host "==> Outside tools (Graphviz, ngspice, KiCad)"
& (Join-Path $venv "Scripts\pcs14.exe") electrical --tools | Select-Object -Skip 1 | ForEach-Object { Write-Host $_ }

Write-Host "==> Lint (same as CI)"
& (Join-Path $venv "Scripts\ruff.exe") check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Tests (same as CI)"
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "All good."
