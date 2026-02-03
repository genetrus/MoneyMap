from pathlib import Path

from money_map.app.api import recommend_variants
from money_map.core.model import Rule, Rulepack, StalenessPolicy, Variant
from money_map.core.recommend import recommend


def test_recommend_deterministic():
    root = Path(__file__).resolve().parents[1]
    result_a = recommend_variants(
        profile_path=root / "profiles" / "demo_fast_start.yaml",
        objective="fastest_money",
        top_n=3,
        data_dir=root / "data",
    )
    result_b = recommend_variants(
        profile_path=root / "profiles" / "demo_fast_start.yaml",
        objective="fastest_money",
        top_n=3,
        data_dir=root / "data",
    )

    ids_a = [rec.variant.variant_id for rec in result_a.ranked_variants]
    ids_b = [rec.variant.variant_id for rec in result_b.ranked_variants]
    assert ids_a == ids_b


def test_recommend_tiebreaker_orders_by_variant_id():
    policy = StalenessPolicy(stale_after_days=365)
    rulepack = Rulepack(
        reviewed_at="2024-01-01",
        staleness_policy=policy,
        compliance_kits={},
        regulated_domains=[],
        rules=[Rule(rule_id="ok.base", reason="baseline")],
    )
    profile = {
        "name": "Demo",
        "language_level": "B2",
        "capital_eur": 500,
        "time_per_week": 10,
        "assets": [],
    }

    def _variant(variant_id: str) -> Variant:
        return Variant(
            variant_id=variant_id,
            title=f"Variant {variant_id}",
            summary="Summary",
            tags=[],
            feasibility={},
            prep_steps=[],
            economics={
                "time_to_first_money_days_range": [30, 30],
                "typical_net_month_eur_range": [500, 500],
                "costs_eur_range": [0, 0],
                "confidence": "medium",
            },
            legal={"legal_gate": "ok", "checklist": []},
            review_date="2024-01-01",
        )

    variants = [_variant("b_variant"), _variant("a_variant")]
    result = recommend(
        profile,
        variants,
        rulepack,
        policy,
        objective_preset="fastest_money",
        filters={},
        top_n=2,
    )

    ids = [rec.variant.variant_id for rec in result.ranked_variants]
    assert ids == ["a_variant", "b_variant"]
