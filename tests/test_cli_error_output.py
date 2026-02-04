from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree

from money_map.storage.fs import read_yaml, write_yaml


def _prepare_invalid_rulepack(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    data_dir = tmp_path / "data"
    copytree(root / "data", data_dir)
    rulepack_path = data_dir / "rulepacks" / "DE.yaml"
    rulepack_payload = read_yaml(rulepack_path)
    rulepack_payload["reviewed_at"] = "not-a-date"
    write_yaml(rulepack_path, rulepack_payload)
    return data_dir


def test_cli_invalid_data_no_traceback(tmp_path: Path) -> None:
    data_dir = _prepare_invalid_rulepack(tmp_path)
    profile_path = Path(__file__).resolve().parents[1] / "profiles" / "demo_fast_start.yaml"
    repo_src = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_src)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "money_map.app.cli",
            "recommend",
            "--profile",
            str(profile_path),
            "--top",
            "1",
            "--data-dir",
            str(data_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    combined = result.stdout + result.stderr
    assert result.returncode != 0, combined
    assert "Traceback" not in combined
    assert "DATA_VALIDATION_ERROR" in combined
