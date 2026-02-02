from money_map.app.api import plan_variant
from money_map.render.plan_md import render_plan_md


def test_plan_contains_compliance_and_artifacts():
    plan = plan_variant(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
    )
    assert len(plan.steps) >= 10
    assert len(plan.artifacts) >= 3
    rendered = render_plan_md(plan)
    assert "## Compliance" in rendered
