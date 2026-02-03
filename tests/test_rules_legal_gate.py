from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.rules import evaluate_legal


def test_rules_force_legal_gate_when_rulepack_stale_and_regulated():
    app_data = load_app_data()
    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    regulated_domains = set(app_data.rulepack.regulated_domains)
    regulated_variant = next(v for v in app_data.variants if regulated_domains.intersection(v.tags))

    legal = evaluate_legal(stale_rulepack, regulated_variant, app_data.meta.staleness_policy)

    assert legal.legal_gate == "require_check"
    assert any("DATA_STALE" in item for item in legal.checklist)
    assert any("require_check_if_stale" in rule.rule_id for rule in legal.applied_rules)


def test_rules_apply_blocked_rule():
    app_data = load_app_data()
    base_variant = app_data.variants[0]
    blocked_variant = replace(base_variant, legal={"legal_gate": "blocked", "checklist": []})

    legal = evaluate_legal(app_data.rulepack, blocked_variant, app_data.meta.staleness_policy)

    assert legal.legal_gate == "blocked"
    assert any(rule.rule_id.startswith("blocked.") for rule in legal.applied_rules)


def test_rules_force_legal_gate_when_variant_date_invalid_and_regulated():
    app_data = load_app_data()
    regulated_domains = set(app_data.rulepack.regulated_domains)
    regulated_variant = next(v for v in app_data.variants if regulated_domains.intersection(v.tags))
    invalid_variant = replace(regulated_variant, review_date="not-a-date")

    legal = evaluate_legal(app_data.rulepack, invalid_variant, app_data.meta.staleness_policy)

    assert legal.legal_gate == "require_check"
    assert any("DATE_INVALID" in item for item in legal.checklist)
    assert any("require_check_if_stale" in rule.rule_id for rule in legal.applied_rules)


def test_rules_apply_blocked_fallback_when_missing():
    app_data = load_app_data()
    base_variant = app_data.variants[0]
    blocked_variant = replace(base_variant, legal={"legal_gate": "blocked", "checklist": []})
    rulepack_without_blocked = replace(
        app_data.rulepack,
        rules=[rule for rule in app_data.rulepack.rules if not rule.rule_id.startswith("blocked.")],
    )

    legal = evaluate_legal(
        rulepack_without_blocked,
        blocked_variant,
        app_data.meta.staleness_policy,
    )

    assert legal.legal_gate == "blocked"
    assert any(rule.rule_id == "blocked.missing_rulepack_rule" for rule in legal.applied_rules)
