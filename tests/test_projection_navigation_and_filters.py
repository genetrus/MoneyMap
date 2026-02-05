from money_map.app.api import plan_variant
from money_map.core.load import load_app_data
from money_map.core.recommend import recommend
from money_map.ui.navigation import NAV_ITEMS


def test_ui_navigation_has_projection_blocks() -> None:
    labels = [label for label, _ in NAV_ITEMS]
    assert labels == [
        "AppData",
        "UserProfile",
        "Variant",
        "Taxonomy/Cells",
        "Bridges/Paths",
        "RulePack",
        "RecommendationResult",
        "RoutePlan",
        "Exports",
    ]


def test_recommend_filters_compliance_mode() -> None:
    app_data = load_app_data()
    profile = {
        "name": "Demo",
        "objective": "fastest_money",
        "language_level": "B2",
        "capital_eur": 500,
        "time_per_week": 15,
        "assets": ["phone", "laptop"],
        "location": "Berlin",
    }
    result = recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        filters={"compliance_mode": "exclude_if_requires_prep"},
        top_n=10,
    )
    assert all(rec.legal.legal_gate == "ok" for rec in result.ranked_variants)


def test_plan_includes_compliance_when_allowed() -> None:
    plan = plan_variant(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.regulated.childcare_assist",
    )
    assert plan.compliance
    assert any("tax_basics" in item for item in plan.compliance)
