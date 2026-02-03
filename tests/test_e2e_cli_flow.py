from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree, which

from money_map.storage.fs import read_yaml, write_yaml
from tests.helpers import count_bullet_lines, count_numbered_lines, extract_section


def _run_cli_module(
    args: list[str], cwd: Path, env: dict[str, str] | None
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "money_map.app.cli", *args]
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

    repo_src = root / "src"
    try:
        import money_map
    except ModuleNotFoundError:
        env["PYTHONPATH"] = str(repo_src)
    else:
        if Path(money_map.__file__ or "").resolve().is_relative_to(repo_src):
            env["PYTHONPATH"] = str(repo_src)

    profile_path = root / "profiles" / "demo_fast_start.yaml"
    data_dir = tmp_path / "data"
    copytree(root / "data", data_dir)
    rulepack_path = data_dir / "rulepacks" / "DE.yaml"
    rulepack_payload = read_yaml(rulepack_path)
    rulepack_payload["reviewed_at"] = "2000-01-01"
    write_yaml(rulepack_path, rulepack_payload)

    variants_payload = read_yaml(data_dir / "variants.yaml")
    variants = variants_payload.get("variants", [])
    tags_by_variant = {variant["variant_id"]: set(variant.get("tags", [])) for variant in variants}
    regulated_domains = set(rulepack_payload.get("regulated_domains", []))
    regulated_variants = {
        variant_id for variant_id, tags in tags_by_variant.items() if tags & regulated_domains
    }

    _run_cli_module(["validate", "--data-dir", str(data_dir)], cwd=root, env=env)

    cli_path = which("money-map", path=env.get("PATH"))
    if cli_path:
        subprocess.run(
            [cli_path, "validate", "--data-dir", str(data_dir)],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

    recommend_first = _run_cli_module(
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
    recommend_second = _run_cli_module(
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

    payload_first = json.loads(recommend_first.stdout)
    payload_second = json.loads(recommend_second.stdout)
    assert payload_first["recommendations"], "Expected at least one recommendation."
    ids_first = [item["variant_id"] for item in payload_first["recommendations"]]
    ids_second = [item["variant_id"] for item in payload_second["recommendations"]]
    assert ids_first == ids_second
    regulated_ranked = [variant_id for variant_id in ids_first if variant_id in regulated_variants]
    assert regulated_ranked, "Expected at least one regulated variant in recommendations."
    variant_id = regulated_ranked[0] if regulated_ranked else ids_first[0]

    _run_cli_module(
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

    _run_cli_module(
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

    plan_md = (tmp_path / "plan.md").read_text(encoding="utf-8")
    steps_section = extract_section(plan_md, "## Steps")
    artifacts_section = extract_section(plan_md, "## Artifacts")
    assert count_numbered_lines(steps_section) >= 10
    assert count_bullet_lines(artifacts_section) >= 3
    artifact_names = {
        line.strip()[2:] for line in artifacts_section if line.strip().startswith("- ")
    }
    assert len({name for name in artifact_names if name}) >= 3

    result_payload = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    legal_payload = result_payload.get("legal", {})
    applied_rules = legal_payload.get("applied_rules", [])
    assert applied_rules, "Expected applied_rules to be present and non-empty."
    legal_gate = str(legal_payload.get("legal_gate", ""))
    if any(
        term in legal_gate
        for term in ("regulated", "require_check", "registration", "license", "blocked")
    ):
        checklist = legal_payload.get("checklist", [])
        assert checklist, "Expected non-empty legal checklist for regulated/blocked gate."
        for kit_name in rulepack_payload.get("compliance_kits", {}):
            assert any(str(item).startswith(f"{kit_name}:") for item in checklist), (
                f"Expected compliance kit {kit_name} in checklist."
            )
