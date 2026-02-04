#!/usr/bin/env python
"""Install UI dependencies with offline/restricted network guidance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> int:
    return subprocess.call(command)  # noqa: S603


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "pip", "install", "-e", ".[ui]"]
    print(f"Running: {' '.join(cmd)} (cwd={repo_root})")
    status = _run(cmd)
    if status == 0:
        print("UI dependencies installed successfully.")
        return 0

    print("\nUI dependency install failed.")
    print("If you are on a restricted network, try one of the following options:")
    print("  1) Retry without build isolation:")
    print('     python -m pip install --no-build-isolation -e ".[ui]"')
    print("  2) Offline wheelhouse install:")
    print("     # On an online machine:")
    print('     python -m pip download -d wheelhouse "money-map[ui]"')
    print("     # On the offline machine (repo root):")
    print('     python -m pip install --no-index --find-links=wheelhouse -e ".[ui]"')
    print("  3) Configure a proxy/mirror for pip before installing.")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
