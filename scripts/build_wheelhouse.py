#!/usr/bin/env python
"""Build a wheelhouse for UI dependencies (offline install support)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _parse_ui_deps(pyproject_path: Path) -> list[str]:
    lines = pyproject_path.read_text(encoding="utf-8").splitlines()
    in_project = False
    in_optional = False
    in_ui = False
    deps: list[str] = []
    base_deps: list[str] = []
    in_dependencies = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            in_optional = stripped == "[project.optional-dependencies]"
            in_ui = False
            in_dependencies = False
            continue
        if in_project:
            if stripped.startswith("dependencies"):
                in_dependencies = True
                if "[" in stripped and "]" in stripped:
                    in_dependencies = False
                continue
            if in_dependencies and stripped.startswith("]"):
                in_dependencies = False
                continue
            if in_dependencies and stripped.startswith('"'):
                base_deps.append(stripped.strip('",'))
            continue
        if in_optional:
            if stripped.startswith("ui"):
                in_ui = True
                if "[" in stripped and "]" in stripped:
                    in_ui = False
                continue
            if in_ui and stripped.startswith("]"):
                in_ui = False
                continue
            if in_ui and stripped.startswith('"'):
                deps.append(stripped.strip('",'))
    return base_deps + deps


def main() -> int:
    parser = argparse.ArgumentParser(description="Build wheelhouse for MoneyMap UI deps")
    parser.add_argument("--out", default="wheelhouse", help="Output directory for wheels")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        print("pyproject.toml not found.")
        return 1

    deps = _parse_ui_deps(pyproject_path)
    extra = ["setuptools>=61", "wheel"]
    if not deps:
        print("No UI dependencies found in pyproject.toml.")
        return 1

    out_dir = repo_root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pip", "download", "-d", str(out_dir), *extra, *deps]
    print(f"Running: {' '.join(cmd)}")
    status = subprocess.call(cmd)  # noqa: S603
    if status != 0:
        print("Wheelhouse build failed.")
        return status

    print("Wheelhouse build complete.")
    print(f"Offline install: python scripts/install_ui_offline.py --wheelhouse {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
