#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="${PYTHON:-python}"

hint_install_failure() {
  cat <<'EOF' >&2
Pip install failed. If you are behind a proxy or offline, try:
  Bash:
    MM_PIP_ARGS="--index-url https://mirror.example.com/simple --trusted-host mirror.example.com" make mvp
    MM_WHEELHOUSE=wheelhouse make mvp
  PowerShell:
    $env:MM_PIP_ARGS="--index-url https://mirror.example.com/simple --trusted-host mirror.example.com"; make mvp
    $env:MM_WHEELHOUSE="wheelhouse"; make mvp
EOF
}

pip_install() {
  local -a args
  local -a extra_args=()

  # shellcheck disable=SC2206
  if [[ -n "${MM_PIP_ARGS:-}" ]]; then
    extra_args=($MM_PIP_ARGS)
  fi

  args=(-m pip install)
  if [[ -n "${MM_WHEELHOUSE:-}" ]]; then
    if [[ ! -d "$MM_WHEELHOUSE" ]]; then
      echo "MM_WHEELHOUSE is set to '$MM_WHEELHOUSE' but the directory does not exist." >&2
      exit 2
    fi
    args+=(--no-index --find-links="$MM_WHEELHOUSE")
  fi
  args+=("${extra_args[@]}" "$@")

  if ! python "${args[@]}"; then
    hint_install_failure
    exit 1
  fi
}

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip_install --upgrade pip
pip_install -e ".[ui]" --no-build-isolation

python -c "import streamlit as st; print('streamlit', st.__version__)"

python scripts/mvp_check.py
