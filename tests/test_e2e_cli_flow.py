from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import which

import pytest

def _run_cli(
    args: list[str], cwd: Path, env: dict[str, str] | None
) -> subprocess.CompletedProcess[str]:
    cli_path = which("money-map", path=env.get("PATH") if env else None)
    command = (
        [cli_path, *args]
        if cli_path
        else [sys.executable, "-m", "money_map.app.cli", *args]
    )
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def test_e2e_cli_flow(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.update(
        {
            "MONEY_MAP_DISABLE_NETWORK": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "NO_COLOR": "1",
            "TERM": "dumb",
            "COLUMNS": "120",
        }
    )

    if which("money-map", path=env.get("PATH")) is None:
        pytest.skip("money-map console script not installed; install package to run CLI E2E.")

    profile_path = root / "profiles" / "demo_fast_start.yaml"
    data_dir = root / "data"

    _run_cli(["validate", "--data-dir", str(data_dir)], cwd=root, env=env)

    recommend = _run_cli(
        [
            "recommend",
            "--profile",
            str(profile_path),
            "--top",
            "10",
            "--objective",
            "fastest_money",
            "--data-dir",
            str(data_dir),
            "--format",
            "json",
        ],
        cwd=root,
        env=env,
    )

    payload = json.loads(recommend.stdout)
    assert payload["recommendations"], "Expected at least one recommendation."
    variant_id = payload["recommendations"][0]["variant_id"]

    _run_cli(
        [
            "plan",
            "--profile",
            str(profile_path),
            "--variant-id",
            variant_id,
            "--data-dir",
            str(data_dir),
        ],
        cwd=root,
        env=env,
    )

    _run_cli(
        [
            "export",
            "--profile",
            str(profile_path),
            "--variant-id",
            variant_id,
            "--out",
            str(tmp_path),
            "--data-dir",
            str(data_dir),
        ],
        cwd=root,
        env=env,
    )

    assert (tmp_path / "plan.md").exists()
    assert (tmp_path / "result.json").exists()
    assert (tmp_path / "profile.yaml").exists()
