from money_map.app.api import plan_variant
from money_map.render.plan_md import render_plan_md


def test_plan_template_v1_contains_required_sections_in_order() -> None:
    plan = plan_variant(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
        data_dir="data",
    )
    rendered = render_plan_md(plan)

    headers = [
        "## 0) Metadata",
        "## 1) Executive summary",
        "## 2) Preconditions & Blockers (feasibility)",
        "## 3) Targets & Success criteria (4 weeks)",
        "## 4) Required artifacts (minimum 3)",
        "## 5) Step-by-step checklist — minimum 10",
        "## 6) 4-week plan (Week 1–4)",
        "## 7) Compliance & Legal checks",
        "## 8) Economics & Tracking (estimate, not guarantee)",
        "## 9) Risks & Mitigations (minimum 5)",
        "## 10) Decision points & Fallbacks",
        "## Appendix A) Evidence & Staleness",
    ]

    positions = [rendered.index(header) for header in headers]
    assert positions == sorted(positions)
    assert "not guarantees" in rendered


def test_plan_template_v1_validates_minimum_quotas() -> None:
    plan = plan_variant(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
        data_dir="data",
    )

    bad_steps = plan.__class__(
        variant_id=plan.variant_id,
        steps=plan.steps[:9],
        artifacts=plan.artifacts,
        week_plan=plan.week_plan,
        compliance=plan.compliance,
        legal_gate=plan.legal_gate,
        applied_rules=plan.applied_rules,
        staleness=plan.staleness,
    )
    try:
        render_plan_md(bad_steps)
        assert False, "expected ValueError for <10 steps"
    except ValueError as exc:
        assert "at least 10 steps" in str(exc)

    bad_artifacts = plan.__class__(
        variant_id=plan.variant_id,
        steps=plan.steps,
        artifacts=plan.artifacts[:2],
        week_plan=plan.week_plan,
        compliance=plan.compliance,
        legal_gate=plan.legal_gate,
        applied_rules=plan.applied_rules,
        staleness=plan.staleness,
    )
    try:
        render_plan_md(bad_artifacts)
        assert False, "expected ValueError for <3 artifacts"
    except ValueError as exc:
        assert "at least 3 artifacts" in str(exc)

    bad_compliance = plan.__class__(
        variant_id=plan.variant_id,
        steps=plan.steps,
        artifacts=plan.artifacts,
        week_plan=plan.week_plan,
        compliance=[],
        legal_gate=plan.legal_gate,
        applied_rules=plan.applied_rules,
        staleness=plan.staleness,
    )
    try:
        render_plan_md(bad_compliance)
        assert False, "expected ValueError for missing compliance"
    except ValueError as exc:
        assert "compliance" in str(exc).lower()
