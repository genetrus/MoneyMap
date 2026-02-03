"""Legal gate and compliance checks."""

from __future__ import annotations

from money_map.core.model import LegalResult, Rule, Rulepack, StalenessPolicy, Variant
from money_map.core.staleness import evaluate_staleness


def evaluate_legal(
    rulepack: Rulepack,
    variant: Variant,
    staleness_policy: StalenessPolicy,
) -> LegalResult:
    legal = variant.legal
    legal_gate = str(legal.get("legal_gate", "ok"))
    checklist = list(legal.get("checklist", []))
    applied_rules: list[Rule] = []

    rulepack_staleness = evaluate_staleness(
        rulepack.reviewed_at,
        staleness_policy,
        label="rulepack",
    )
    variant_staleness = evaluate_staleness(
        variant.review_date,
        staleness_policy,
        label=f"variant:{variant.variant_id}",
    )
    stale = rulepack_staleness.is_stale or variant_staleness.is_stale
    regulated = any(tag in rulepack.regulated_domains for tag in variant.tags)
    if stale and regulated:
        legal_gate = "require_check"
        checklist.append("DATA_STALE: re-verify laws before launch.")
        for rule in rulepack.rules:
            if "require_check_if_stale" in rule.rule_id:
                applied_rules.append(rule)

    if legal_gate == "blocked":
        blocked_rules = [rule for rule in rulepack.rules if rule.rule_id.startswith("blocked.")]
        if not blocked_rules:
            checklist.append("Rulepack has no explicit blocked rule; manual review required.")
            blocked_rules.append(
                Rule(
                    rule_id="blocked.missing_rulepack_rule",
                    reason="Legal gate blocked but rulepack lacks an explicit blocked rule.",
                )
            )
        applied_rules.extend(blocked_rules)

    return LegalResult(legal_gate=legal_gate, checklist=checklist, applied_rules=applied_rules)
