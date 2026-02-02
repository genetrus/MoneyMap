$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvDir = Join-Path $RootDir ".venv"
$PythonExe = if ($env:PYTHON) { $env:PYTHON } else { "python" }

if (-not (Test-Path $VenvDir)) {
  & $PythonExe -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[dev,ui]"

& $VenvPython -m ruff format --check .
& $VenvPython -m ruff check .
& $VenvPython -m pytest -q
