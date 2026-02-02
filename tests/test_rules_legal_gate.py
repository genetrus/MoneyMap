from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.rules import evaluate_legal


def test_rules_force_legal_gate_when_rulepack_stale_and_regulated():
    app_data = load_app_data()
    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    regulated_variant = next(v for v in app_data.variants if "regulated" in v.tags)

    legal = evaluate_legal(stale_rulepack, regulated_variant)

    assert legal.legal_gate == "require_check"
    assert any("Rulepack is stale" in item for item in legal.checklist)
    assert any("require_check_if_stale" in rule.rule_id for rule in legal.applied_rules)


def test_rules_apply_blocked_rule():
    app_data = load_app_data()
    base_variant = app_data.variants[0]
    blocked_variant = replace(base_variant, legal={"legal_gate": "blocked", "checklist": []})

    legal = evaluate_legal(app_data.rulepack, blocked_variant)

    assert legal.legal_gate == "blocked"
    assert any("blocked" in rule.rule_id for rule in legal.applied_rules)
