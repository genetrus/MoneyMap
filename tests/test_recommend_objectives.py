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


def test_recommend_objectives_rankings():
    fast_variant = Variant(
        variant_id="fast",
        title="Fast money",
        summary="Fast",
        tags=[],
        feasibility={},
        prep_steps=[],
        economics={
            "time_to_first_money_days_range": [3, 7],
            "typical_net_month_eur_range": [200, 400],
            "costs_eur_range": [0, 50],
        },
        legal={},
        review_date="2026-01-01",
    )
    high_net_variant = Variant(
        variant_id="high_net",
        title="High net",
        summary="High",
        tags=[],
        feasibility={},
        prep_steps=[],
        economics={
            "time_to_first_money_days_range": [20, 30],
            "typical_net_month_eur_range": [1200, 1600],
            "costs_eur_range": [100, 200],
        },
        legal={},
        review_date="2026-01-01",
    )
    profile = {"language_level": "B1", "capital_eur": 0, "time_per_week": 5, "assets": []}
    rulepack = _rulepack()
    policy = StalenessPolicy(stale_after_days=180)

    fastest = recommend(
        profile, [fast_variant, high_net_variant], rulepack, policy, "fastest_money"
    )
    max_net = recommend(profile, [fast_variant, high_net_variant], rulepack, policy, "max_net")

    assert fastest.ranked_variants[0].variant.variant_id == "fast"
    assert max_net.ranked_variants[0].variant.variant_id == "high_net"


def test_recommend_objective_preset_is_deterministic_for_same_inputs():
    fast_variant = Variant(
        variant_id="a_fast",
        title="A",
        summary="A",
        tags=[],
        feasibility={"min_time_per_week": 1, "min_capital": 0, "required_assets": []},
        prep_steps=[],
        economics={
            "time_to_first_money_days_range": [7, 7],
            "typical_net_month_eur_range": [500, 500],
            "costs_eur_range": [0, 0],
            "confidence": "medium",
        },
        legal={"legal_gate": "ok", "checklist": []},
        review_date="2026-01-01",
    )
    profile = {"language_level": "B1", "capital_eur": 200, "time_per_week": 10, "assets": []}
    rulepack = _rulepack()
    policy = StalenessPolicy(stale_after_days=180)

    result_a = recommend(profile, [fast_variant], rulepack, policy, "balanced")
    result_b = recommend(profile, [fast_variant], rulepack, policy, "balanced")

    assert len(result_a.ranked_variants) == 1
    assert result_a.ranked_variants[0].score == result_b.ranked_variants[0].score
