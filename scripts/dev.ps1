$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvDir = Join-Path $RootDir ".venv"
$PythonExe = if ($env:PYTHON) { $env:PYTHON } else { "python" }

if (-not (Test-Path $VenvDir)) {
  & $PythonExe -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvMoneyMapExe = Join-Path $VenvDir "Scripts\money-map.exe"

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[ui]"

if (Test-Path $VenvMoneyMapExe) {
  & $VenvMoneyMapExe --help
} else {
  & $VenvPython -m money_map --help
}

Write-Host "UI command is not implemented yet. When available, run: money-map ui"
