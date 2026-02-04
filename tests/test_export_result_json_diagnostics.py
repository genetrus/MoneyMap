from __future__ import annotations

import json
from pathlib import Path

from money_map.app.api import export_bundle


def test_export_result_contains_diagnostics_and_rules(tmp_path: Path) -> None:
    paths = export_bundle(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
        out_dir=tmp_path,
    )

    result_payload = json.loads(Path(paths["result"]).read_text(encoding="utf-8"))
    assert "diagnostics" in result_payload
    assert "timings_ms" in result_payload["diagnostics"]
    assert "legal" in result_payload
    assert "applied_rules" in result_payload["legal"]
    assert "applied_rule_ids" in result_payload["legal"]
    assert isinstance(result_payload["legal"]["applied_rules"], list)
    if result_payload["legal"]["applied_rules"]:
        first_rule = result_payload["legal"]["applied_rules"][0]
        assert "rule_id" in first_rule
        assert "reason" in first_rule
