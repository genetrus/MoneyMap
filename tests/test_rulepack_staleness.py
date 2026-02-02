from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.validate import validate


def test_rulepack_and_variant_staleness_warns():
    app_data = load_app_data()
    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    stale_variant = replace(app_data.variants[0], review_date="2000-01-01")
    app_data = replace(app_data, rulepack=stale_rulepack, variants=[stale_variant])

    report = validate(app_data)

    assert "STALE_RULEPACK" in report.warns
    assert any(warn.startswith("STALE_VARIANTS:") for warn in report.warns)
