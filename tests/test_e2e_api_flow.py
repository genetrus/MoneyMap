from __future__ import annotations

from pathlib import Path

from money_map.app.api import export_bundle, recommend_variants
from tests.helpers import (
    block_network,
    count_bullet_lines,
    count_numbered_lines,
    extract_section,
)


def test_e2e_api_flow(tmp_path: Path, monkeypatch) -> None:
    block_network(monkeypatch)
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    profile_path = root / "profiles" / "demo_fast_start.yaml"
    assert profile_path.exists(), "Expected demo profile at profiles/demo_fast_start.yaml"
    data_dir = root / "data"

    first = recommend_variants(
        profile_path=profile_path,
        objective="fastest_money",
        top_n=10,
        data_dir=data_dir,
    )
    second = recommend_variants(
        profile_path=profile_path,
        objective="fastest_money",
        top_n=10,
        data_dir=data_dir,
    )

    ids_first = [rec.variant.variant_id for rec in first.ranked_variants]
    ids_second = [rec.variant.variant_id for rec in second.ranked_variants]
    assert ids_first == ids_second
    assert 1 <= len(ids_first) <= 10

    export_paths = export_bundle(
        profile_path=profile_path,
        variant_id=ids_first[0],
        out_dir=tmp_path,
        data_dir=data_dir,
    )

    plan_path = Path(export_paths["plan"])
    result_path = Path(export_paths["result"])
    profile_out_path = Path(export_paths["profile"])
    assert plan_path.exists()
    assert result_path.exists()
    assert profile_out_path.exists()

    artifacts = [Path(path) for path in export_paths["artifacts"]]
    assert artifacts, "Expected placeholder artifacts for Release 0.1"
    for artifact in artifacts:
        assert artifact.exists()
        assert "artifacts" in artifact.as_posix()

    plan_md = plan_path.read_text(encoding="utf-8")
    assert "## Compliance" in plan_md
    assert "Prep tasks" in plan_md

    steps_section = extract_section(plan_md, "## Steps")
    artifacts_section = extract_section(plan_md, "## Artifacts")

    assert count_numbered_lines(steps_section) >= 10
    assert count_bullet_lines(artifacts_section) >= 3
    assert any("artifacts/" in line for line in artifacts_section)
