#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="${PYTHON:-python}"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

MONEY_MAP_DISABLE_NETWORK=1 python -m money_map.app.cli validate --data-dir data
MONEY_MAP_DISABLE_NETWORK=1 python -m pytest -q tests/test_e2e_api_flow.py tests/test_e2e_cli_flow.py
