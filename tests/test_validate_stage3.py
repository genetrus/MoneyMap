from __future__ import annotations

from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.model import Rule
from money_map.core.validate import validate


def _codes(items: list[dict]) -> set[str]:
    return {item.get("code", "") for item in items}


def test_validate_detects_duplicate_variant_id_fatal() -> None:
    app_data = load_app_data()
    duplicate = replace(app_data.variants[0], title="Duplicate")
    patched = replace(app_data, variants=[*app_data.variants, duplicate])

    report = validate(patched)

    assert "VARIANT_ID_DUPLICATE" in _codes(report.fatals)
    assert report.status == "invalid"


def test_validate_warns_on_unknown_legal_gate_and_bad_ranges() -> None:
    app_data = load_app_data()
    v = app_data.variants[0]
    bad_variant = replace(
        v,
        economics={
            **v.economics,
            "time_to_first_money_days_range": [20, 5],
            "typical_net_month_eur_range": [1000, 200],
            "costs_eur_range": "oops",
            "confidence": "certain",
        },
        legal={**v.legal, "legal_gate": "auto-approved"},
    )

    report = validate(replace(app_data, variants=[bad_variant, *app_data.variants[1:]]))
    warn_codes = _codes(report.warns)

    assert "VARIANT_ECONOMICS_TIME_RANGE_INVALID_ORDER" in warn_codes
    assert "VARIANT_ECONOMICS_NET_RANGE_INVALID_ORDER" in warn_codes
    assert "VARIANT_ECONOMICS_COST_RANGE_INVALID" in warn_codes
    assert "VARIANT_ECONOMICS_CONFIDENCE_UNKNOWN" in warn_codes
    assert "VARIANT_LEGAL_GATE_UNKNOWN" in warn_codes


def test_validate_warns_on_unknown_rule_reference() -> None:
    app_data = load_app_data()
    v = app_data.variants[0]
    patched_variant = replace(v, legal={**v.legal, "rule_ids": ["missing.rule"]})

    report = validate(replace(app_data, variants=[patched_variant, *app_data.variants[1:]]))

    assert "VARIANT_RULE_REF_UNKNOWN" in _codes(report.warns)


def test_validate_detects_duplicate_rulepack_rule_id_fatal() -> None:
    app_data = load_app_data()
    dup_rule = Rule(rule_id=app_data.rulepack.rules[0].rule_id, reason="duplicate")
    patched_rulepack = replace(app_data.rulepack, rules=[*app_data.rulepack.rules, dup_rule])

    report = validate(replace(app_data, rulepack=patched_rulepack))

    assert "RULEPACK_RULE_ID_DUPLICATE" in _codes(report.fatals)
    assert report.status == "invalid"


def test_validate_warns_on_negative_feasibility_values() -> None:
    app_data = load_app_data()
    v = app_data.variants[0]
    patched_variant = replace(
        v,
        feasibility={**v.feasibility, "min_capital": -1, "min_time_per_week": -5},
    )

    report = validate(replace(app_data, variants=[patched_variant, *app_data.variants[1:]]))

    assert "VARIANT_FEASIBILITY_NEGATIVE_VALUE" in _codes(report.warns)
