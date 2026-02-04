#!/usr/bin/env python
"""Install UI dependencies from a local wheelhouse (offline)."""

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


def _run(cmd: list[str]) -> int:
    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)  # noqa: S603


def main() -> int:
    parser = argparse.ArgumentParser(description="Install MoneyMap UI deps from wheelhouse")
    parser.add_argument("--wheelhouse", required=True, help="Path to wheelhouse directory")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    wheelhouse = Path(args.wheelhouse).resolve()
    if not wheelhouse.exists():
        print(f"Wheelhouse not found: {wheelhouse}")
        return 1

    pyproject_path = repo_root / "pyproject.toml"
    deps = _parse_ui_deps(pyproject_path)
    if not deps:
        print("No UI dependencies found in pyproject.toml.")
        return 1

    find_links = ["--no-index", "--find-links", str(wheelhouse)]
    if _run([sys.executable, "-m", "pip", "install", *find_links, "setuptools>=61", "wheel"]) != 0:
        return 1
    if _run([sys.executable, "-m", "pip", "install", *find_links, *deps]) != 0:
        return 1
    if (
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                *find_links,
                "--no-build-isolation",
                "-e",
                ".[ui]",
            ]
        )
        != 0
    ):
        return 1
    if _run([sys.executable, "-c", "import streamlit as st; print(st.__version__)"]) != 0:
        return 1

    print("Offline UI dependency install complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
