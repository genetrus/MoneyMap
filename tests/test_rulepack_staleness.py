from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.rules import evaluate_legal
from money_map.core.validate import validate


def _issue_codes(issues: list[dict]) -> list[str]:
    return [issue.get("code", "") for issue in issues if issue.get("code")]


def test_rulepack_and_variant_staleness_warns():
    app_data = load_app_data()
    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    stale_variant = replace(app_data.variants[0], review_date="2000-01-01")
    app_data = replace(app_data, rulepack=stale_rulepack, variants=[stale_variant])

    report = validate(app_data)

    warn_codes = _issue_codes(report.warns)
    assert "STALE_RULEPACK" in warn_codes or "STALE_RULEPACK_HARD" in warn_codes
    assert "STALE_VARIANTS" in warn_codes


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

    fatal_codes = _issue_codes(report.fatals)
    warn_codes = _issue_codes(report.warns)
    assert "RULEPACK_REVIEWED_AT_INVALID" not in fatal_codes
    assert "VARIANT_REVIEW_DATE_INVALID" in warn_codes

    legal = evaluate_legal(app_data.rulepack, invalid_variant, app_data.meta.staleness_policy)
    assert legal.legal_gate == "require_check"
    assert any("DATE_INVALID" in item for item in legal.checklist)
