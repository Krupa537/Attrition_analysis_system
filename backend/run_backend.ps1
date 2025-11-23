# Helper script to create venv, install dependencies, and start the API
# Usage: Open PowerShell in this folder and run: ./run_backend.ps1

param(
    [int]$Port = 8000,
    [string]$BindHost = '0.0.0.0',
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'

Write-Host "Running backend setup in: $(Get-Location)"

# Choose python launcher if available
$pyCmd = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }

try {
    Write-Host "Creating virtual environment (.venv) using: $pyCmd"
    & $pyCmd -3 -m venv .venv
} catch {
    Write-Warning "Failed to create venv with $pyCmd; will try using 'python -m venv' as fallback"
    & python -m venv .venv
}

if (-Not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Warning "Virtualenv activation script not found. If venv creation failed, consider deleting any existing '.venv' and retrying."
}

Write-Host "Activating virtualenv..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

$reloadFlag = if ($NoReload) { '' } else { '--reload' }
$useReload = -not $NoReload
Write-Host "Starting uvicorn on ${BindHost}:${Port} (reload: $useReload)..."
python -m uvicorn app.main:app $reloadFlag --host $BindHost --port $Port
