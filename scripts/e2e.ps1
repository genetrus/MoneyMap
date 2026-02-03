$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path "$PSScriptRoot\..").Path
$VenvDir = Join-Path $RootDir ".venv"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}

& "$VenvDir\Scripts\Activate.ps1"

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

$env:MONEY_MAP_DISABLE_NETWORK = "1"
python -m money_map.app.cli validate --data-dir data
python -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py
