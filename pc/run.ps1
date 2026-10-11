$ErrorActionPreference = 'Stop'

$projectDir = $PSScriptRoot
$venvPython = Join-Path $projectDir '.venv\Scripts\python.exe'
$env:PYTHONPATH = Join-Path $projectDir 'src'

if (Test-Path $venvPython) {
    & $venvPython (Join-Path $projectDir 'main.py') @args
}
else {
    & py -3 (Join-Path $projectDir 'main.py') @args
}
if ($LASTEXITCODE -ne 0) {
    throw 'SignalScope exited with an error. Install its dependencies with .\install.ps1.'
}
