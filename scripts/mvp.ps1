$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path "$PSScriptRoot\..").Path
$VenvDir = Join-Path $RootDir ".venv"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}

& "$VenvDir\Scripts\Activate.ps1"

python -m pip install --upgrade pip
python -m pip install -e ".[ui]" --no-build-isolation

python -c "import streamlit as st; print('streamlit', st.__version__)"

python scripts/mvp_check.py
