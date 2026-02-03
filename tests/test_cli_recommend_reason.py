from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree

from money_map.storage.fs import read_yaml, write_yaml


def _is_regulated_variant(variant: dict, regulated_domains: set[str]) -> bool:
    tags = set(variant.get("tags", []))
    return bool(tags.intersection(regulated_domains)) or "regulated" in tags


def test_cli_recommend_includes_date_invalid_reason(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    data_dir = tmp_path / "data"
    copytree(root / "data", data_dir)
    rulepack_path = data_dir / "rulepacks" / "DE.yaml"
    rulepack_payload = read_yaml(rulepack_path)
    regulated_domains = set(rulepack_payload.get("regulated_domains", []))

    variants_path = data_dir / "variants.yaml"
    variants_payload = read_yaml(variants_path)
    variants = variants_payload.get("variants", [])
    regulated_variant = next(
        variant for variant in variants if _is_regulated_variant(variant, regulated_domains)
    )
    regulated_variant["review_date"] = "not-a-date"
    variants_payload["variants"] = [regulated_variant]
    write_yaml(variants_path, variants_payload)

    profile_path = root / "profiles" / "demo_fast_start.yaml"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
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
            "--objective",
            "fastest_money",
            "--data-dir",
            str(data_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "Reason:" in combined
    assert "DATE_INVALID" in combined
