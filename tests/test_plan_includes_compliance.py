from __future__ import annotations

from money_map.app.api import plan_variant


def test_plan_includes_compliance() -> None:
    plan = plan_variant(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
    )
    assert plan.compliance
