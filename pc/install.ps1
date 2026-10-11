$ErrorActionPreference = 'Stop'

$projectDir = $PSScriptRoot
$venvPython = Join-Path $projectDir '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    & py -3 -m venv (Join-Path $projectDir '.venv')
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not create a Python virtual environment. Install Python 3.10+ and retry.'
    }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Failed to upgrade pip.' }

& $venvPython -m pip install -e $projectDir
if ($LASTEXITCODE -ne 0) { throw 'Failed to install SignalScope dependencies.' }

Write-Host 'SignalScope setup complete. Launch it with: .\run.ps1'
