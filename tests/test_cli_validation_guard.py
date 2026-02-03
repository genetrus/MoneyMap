from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree

import pytest

from money_map.storage.fs import read_yaml, write_yaml


def _prepare_invalid_rulepack(tmp_path: Path) -> tuple[Path, str]:
    root = Path(__file__).resolve().parents[1]
    data_dir = tmp_path / "data"
    copytree(root / "data", data_dir)
    rulepack_path = data_dir / "rulepacks" / "DE.yaml"
    rulepack_payload = read_yaml(rulepack_path)
    rulepack_payload["reviewed_at"] = "not-a-date"
    write_yaml(rulepack_path, rulepack_payload)
    variants_payload = read_yaml(data_dir / "variants.yaml")
    variant_id = variants_payload["variants"][0]["variant_id"]
    return data_dir, variant_id


@pytest.mark.parametrize("command", ["recommend", "plan", "export"])
def test_cli_blocks_actions_on_validation_fatals(tmp_path: Path, command: str) -> None:
    data_dir, variant_id = _prepare_invalid_rulepack(tmp_path)
    profile_path = Path(__file__).resolve().parents[1] / "profiles" / "demo_fast_start.yaml"
    repo_src = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_src)
    args = [sys.executable, "-m", "money_map.app.cli", command]
    args.extend(["--profile", str(profile_path), "--data-dir", str(data_dir)])
    if command in {"plan", "export"}:
        args.extend(["--variant-id", variant_id])
    if command == "export":
        args.extend(["--out", str(tmp_path / "exports")])

    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    combined = result.stdout + result.stderr
    assert result.returncode != 0, combined
    assert "RULEPACK_REVIEWED_AT_INVALID" in combined
