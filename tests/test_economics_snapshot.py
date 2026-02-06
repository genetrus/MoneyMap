from money_map.core.economics import assess_economics
from money_map.core.model import Variant


def test_economics_snapshot_fields():
    variant = Variant(
        variant_id="econ",
        title="Economics",
        summary="Economics",
        tags=[],
        feasibility={},
        prep_steps=[],
        economics={
            "time_to_first_money_days_range": [5, 10],
            "typical_net_month_eur_range": [300, 600],
            "costs_eur_range": [50, 120],
            "volatility_or_seasonality": "seasonal",
            "variable_costs": "materials",
            "scaling_ceiling": "local capacity",
            "confidence": "medium",
        },
        legal={},
        review_date="2026-01-01",
    )

    economics = assess_economics(variant)

    assert economics.time_to_first_money_days_range == [5, 10]
    assert economics.typical_net_month_eur_range == [300, 600]
    assert economics.costs_eur_range == [50, 120]
    assert economics.volatility_or_seasonality == "seasonal"
    assert economics.variable_costs == "materials"
    assert economics.scaling_ceiling == "local capacity"
    assert economics.confidence == "medium"


def test_economics_snapshot_normalizes_invalid_payloads() -> None:
    variant = Variant(
        variant_id="econ-bad",
        title="Economics Bad",
        summary="Economics Bad",
        tags=[],
        feasibility={},
        prep_steps=[],
        economics={
            "time_to_first_money_days_range": [12, 4],
            "typical_net_month_eur_range": "unknown",
            "costs_eur_range": ["10", 20],
            "volatility": "high",
            "confidence": "certain",
        },
        legal={},
        review_date="2026-01-01",
    )

    economics = assess_economics(variant)

    assert economics.time_to_first_money_days_range == [4, 12]
    assert economics.typical_net_month_eur_range == [0, 0]
    assert economics.costs_eur_range == [0, 0]
    assert economics.volatility_or_seasonality == "high"
    assert economics.confidence == "unknown"
