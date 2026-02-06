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


def test_recommend_explanations_have_expected_lengths() -> None:
    variant = Variant(
        variant_id="v1",
        title="Variant",
        summary="Summary",
        tags=[],
        feasibility={"min_time_per_week": 1, "min_capital": 0, "required_assets": []},
        prep_steps=[],
        economics={
            "time_to_first_money_days_range": [7, 14],
            "typical_net_month_eur_range": [400, 600],
            "costs_eur_range": [0, 50],
            "confidence": "medium",
        },
        legal={"legal_gate": "ok", "checklist": []},
        review_date="2026-01-01",
    )
    profile = {
        "language_level": "B1",
        "capital_eur": 100,
        "time_per_week": 10,
        "assets": [],
        "constraints": [],
    }

    result = recommend(profile, [variant], _rulepack(), StalenessPolicy(stale_after_days=180))

    assert len(result.ranked_variants) == 1
    rec = result.ranked_variants[0]
    assert len(rec.pros) == 3
    assert 1 <= len(rec.cons) <= 2
