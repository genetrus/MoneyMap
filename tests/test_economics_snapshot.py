from money_map.core.economics import assess_economics
from money_map.core.model import Variant


def test_economics_snapshot_fields():
    variant = Variant(
        variant_id="econ",
        title="Economics",
        summary="Economics",
        tags=[],
        taxonomy_id="M00",
        cells=["cell_1"],
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
