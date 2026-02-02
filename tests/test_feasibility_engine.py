from money_map.core.feasibility import assess_feasibility
from money_map.core.model import Variant


def test_feasibility_language_ordering_and_status():
    variant = Variant(
        variant_id="test.variant",
        title="Test",
        summary="Test",
        tags=[],
        feasibility={
            "min_language_level": "A2",
            "min_capital": 500,
            "min_time_per_week": 1,
            "required_assets": [],
        },
        prep_steps=[],
        economics={},
        legal={},
        review_date="2026-01-01",
    )
    profile = {
        "language_level": "B1",
        "capital_eur": 100,
        "time_per_week": 5,
        "assets": [],
    }

    result = assess_feasibility(profile, variant)
    assert result.status == "feasible_with_prep"
    assert result.blockers
    assert len(result.blockers) <= 3
