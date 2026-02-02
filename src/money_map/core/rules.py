"""Legal gate and compliance checks."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from money_map.core.model import LegalResult, Rule, Rulepack, Variant

_DATE_FORMATS = ["%Y-%m-%d"]


def _parse_date(value: str) -> date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _is_stale(rulepack: Rulepack) -> bool:
    reviewed = _parse_date(rulepack.reviewed_at)
    if not reviewed:
        return False
    stale_after = timedelta(days=rulepack.staleness_policy.stale_after_days)
    return date.today() - reviewed > stale_after


def evaluate_legal(rulepack: Rulepack, variant: Variant) -> LegalResult:
    legal = variant.legal
    legal_gate = str(legal.get("legal_gate", "ok"))
    checklist = list(legal.get("checklist", []))
    applied_rules: list[Rule] = []

    stale = _is_stale(rulepack)
    regulated = any(tag in rulepack.regulated_domains for tag in variant.tags)
    if stale and regulated:
        legal_gate = "require_check"
        checklist.append("Rulepack is stale; verify regulations before launch.")
        for rule in rulepack.rules:
            if "require_check_if_stale" in rule.rule_id:
                applied_rules.append(rule)

    if legal_gate == "blocked":
        blocked_rules = [rule for rule in rulepack.rules if "blocked" in rule.rule_id]
        applied_rules.extend(blocked_rules)

    return LegalResult(legal_gate=legal_gate, checklist=checklist, applied_rules=applied_rules)
