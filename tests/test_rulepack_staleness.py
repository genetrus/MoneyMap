from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.rules import evaluate_legal
from money_map.core.validate import validate


def test_rulepack_and_variant_staleness_warns():
    app_data = load_app_data()
    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    stale_variant = replace(app_data.variants[0], review_date="2000-01-01")
    app_data = replace(app_data, rulepack=stale_rulepack, variants=[stale_variant])

    report = validate(app_data)

    assert "STALE_RULEPACK" in report.warns
    assert any(warn.startswith("STALE_VARIANTS:") for warn in report.warns)


def _is_regulated_variant(tags: set[str], regulated_domains: set[str]) -> bool:
    return bool(tags.intersection(regulated_domains)) or "regulated" in tags


def test_variant_invalid_date_warns_and_regulated_requires_check():
    app_data = load_app_data()
    regulated_domains = set(app_data.rulepack.regulated_domains)
    regulated_variant = next(
        variant
        for variant in app_data.variants
        if _is_regulated_variant(set(variant.tags), regulated_domains)
    )
    invalid_variant = replace(regulated_variant, review_date="not-a-date")
    app_data = replace(app_data, variants=[invalid_variant])

    report = validate(app_data)

    assert "RULEPACK_REVIEWED_AT_INVALID" not in report.fatals
    assert any(
        warn.startswith(f"VARIANT_REVIEW_DATE_INVALID:{invalid_variant.variant_id}")
        for warn in report.warns
    )

    legal = evaluate_legal(app_data.rulepack, invalid_variant, app_data.meta.staleness_policy)
    assert legal.legal_gate == "require_check"
    assert any("DATE_INVALID" in item for item in legal.checklist)
