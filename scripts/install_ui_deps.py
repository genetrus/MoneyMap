#!/usr/bin/env python
"""Install UI dependencies with offline/restricted network guidance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(command: list[str], cwd: Path | None = None) -> int:
    print(f"Running: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=cwd)  # noqa: S603
    return completed.returncode


def _run_python(args: list[str], cwd: Path | None = None) -> int:
    return _run([sys.executable, *args], cwd=cwd)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    print(f"Python executable: {sys.executable}", flush=True)
    _run_python(["-m", "pip", "--version"])
    upgrade_status = _run_python(["-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])
    if upgrade_status != 0:
        print("Warning: failed to upgrade pip/setuptools/wheel. Continuing.", flush=True)

    status = _run_python(["-m", "pip", "install", "-e", ".[ui]"], cwd=repo_root)
    if status != 0:
        print("Retrying without build isolation...")
        status = _run_python(
            ["-m", "pip", "install", "--no-build-isolation", "-e", ".[ui]"], cwd=repo_root
        )

    if status != 0:
        print("\nUI dependency install failed. Collecting diagnostics...")
        _run_python(["-m", "pip", "debug", "-v"])
        _run_python(["-m", "pip", "config", "list", "-v"])
        _run_python(["-m", "pip", "-vvv", "install", "-e", ".[ui]"], cwd=repo_root)
        print("\nNext steps:")
        print("  1) Configure a proxy/mirror for pip before installing.")
        print("  2) Offline wheelhouse install:")
        print("     # On an online machine:")
        print("     python scripts/build_wheelhouse.py --out wheelhouse")
        print("     # On the offline machine (repo root):")
        print("     python scripts/install_ui_offline.py --wheelhouse wheelhouse")
        return status

    verify_status = _run_python(
        ["-c", "import streamlit as st; print('streamlit', st.__version__)"]
    )
    if verify_status != 0:
        print("Streamlit import failed after install.")
        return verify_status

    print("UI dependencies installed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
