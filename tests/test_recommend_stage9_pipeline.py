from money_map.core.model import Rulepack, StalenessPolicy, Variant
from money_map.core.recommend import recommend


def _rulepack() -> Rulepack:
    return Rulepack(
        reviewed_at="2026-01-01",
        staleness_policy=StalenessPolicy(stale_after_days=180),
        compliance_kits={},
        regulated_domains=[],
        rules=[],
    )


def _variant(
    variant_id: str,
    *,
    min_time: int = 1,
    min_capital: int = 0,
    required_assets: list[str] | None = None,
    tags: list[str] | None = None,
) -> Variant:
    return Variant(
        variant_id=variant_id,
        title=variant_id,
        summary=variant_id,
        tags=tags or [],
        feasibility={
            "min_language_level": "A2",
            "min_capital": min_capital,
            "min_time_per_week": min_time,
            "required_assets": required_assets or [],
        },
        prep_steps=["step1"],
        economics={
            "time_to_first_money_days_range": [3, 6],
            "typical_net_month_eur_range": [200, 300],
            "costs_eur_range": [0, 50],
            "confidence": "medium",
        },
        legal={"legal_gate": "ok", "checklist": []},
        review_date="2026-01-01",
    )


def test_candidate_generation_filters_regulated_by_constraints() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "capital_eur": 300,
        "time_per_week": 10,
        "assets": ["phone"],
        "constraints": ["no_regulated_domains"],
    }
    regulated = _variant("regulated", tags=["regulated"])
    normal = _variant("normal")

    result = recommend(
        profile,
        [regulated, normal],
        _rulepack(),
        StalenessPolicy(stale_after_days=180),
        objective_preset="fastest_money",
        filters={},
        top_n=5,
    )

    ids = [item.variant.variant_id for item in result.ranked_variants]
    assert ids == ["normal"]
    assert result.diagnostics["reasons"].get("constraint_regulated", 0) == 1


def test_candidate_generation_filters_missing_assets_when_profile_has_none() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "capital_eur": 300,
        "time_per_week": 10,
        "assets": [],
        "constraints": [],
    }
    needs_assets = _variant("needs-assets", required_assets=["laptop"])
    no_assets_needed = _variant("no-assets")

    result = recommend(
        profile,
        [needs_assets, no_assets_needed],
        _rulepack(),
        StalenessPolicy(stale_after_days=180),
        objective_preset="fastest_money",
        filters={},
        top_n=5,
    )

    ids = [item.variant.variant_id for item in result.ranked_variants]
    assert ids == ["no-assets"]
    assert result.diagnostics["reasons"].get("missing_assets_all", 0) == 1


def test_feasibility_not_feasible_filtered_when_requested() -> None:
    profile = {
        "country": "DE",
        "language_level": "A2",
        "capital_eur": 0,
        "time_per_week": 1,
        "assets": ["phone"],
        "constraints": [],
    }
    feasible = _variant("feasible", min_time=1, min_capital=0, required_assets=["phone"])
    impossible = _variant(
        "impossible",
        min_time=30,
        min_capital=2000,
        required_assets=["laptop", "car"],
    )

    result = recommend(
        profile,
        [impossible, feasible],
        _rulepack(),
        StalenessPolicy(stale_after_days=180),
        objective_preset="fastest_money",
        filters={"exclude_not_feasible": True},
        top_n=5,
    )

    ids = [item.variant.variant_id for item in result.ranked_variants]
    assert ids == ["feasible"]
    assert result.diagnostics["reasons"].get("not_feasible", 0) == 1


def test_pipeline_c_emits_economics_snapshot_warnings_for_unknown_ranges() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "capital_eur": 300,
        "time_per_week": 10,
        "assets": ["phone"],
        "constraints": [],
    }
    bad_econ = Variant(
        variant_id="bad-econ",
        title="bad-econ",
        summary="bad-econ",
        tags=[],
        feasibility={
            "min_language_level": "A2",
            "min_capital": 0,
            "min_time_per_week": 1,
            "required_assets": [],
        },
        prep_steps=["step1"],
        economics={"confidence": "low"},
        legal={"legal_gate": "ok", "checklist": []},
        review_date="2026-01-01",
    )

    result = recommend(
        profile,
        [bad_econ],
        _rulepack(),
        StalenessPolicy(stale_after_days=180),
        objective_preset="fastest_money",
        filters={},
        top_n=5,
    )

    assert len(result.ranked_variants) == 1
    econ = result.ranked_variants[0].economics
    assert econ.time_to_first_money_days_range == [0, 0]
    assert econ.typical_net_month_eur_range == [0, 0]
    assert econ.costs_eur_range == [0, 0]
    assert result.diagnostics["warnings"].get("economics_first_money_unknown", 0) == 1
    assert result.diagnostics["warnings"].get("economics_net_unknown", 0) == 1
    assert result.diagnostics["warnings"].get("economics_costs_unknown", 0) == 1
