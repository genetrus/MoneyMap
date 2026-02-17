"""Legal gate and compliance checks."""

from __future__ import annotations

from money_map.core.model import LegalResult, Rule, Rulepack, StalenessPolicy, Variant
from money_map.core.staleness import evaluate_staleness, is_freshness_unknown

ALLOWED_LEGAL_GATES = {"ok", "require_check", "registration", "license", "blocked"}


def _normalized_legal_gate(raw_gate: object) -> str:
    gate = str(raw_gate or "ok").strip().lower()
    if gate in ALLOWED_LEGAL_GATES:
        return gate
    return "require_check"


def _select_compliance_kits(rulepack: Rulepack, legal_gate: str, regulated: bool) -> list[str]:
    available = set(rulepack.compliance_kits.keys())
    baseline = [kit for kit in ("tax_basics", "invoicing_basics") if kit in available]
    expanded = [
        kit for kit in ("tax_basics", "invoicing_basics", "insurance_basics") if kit in available
    ]

    if legal_gate in {"require_check", "registration", "license", "blocked"} or regulated:
        return expanded or sorted(available)
    return baseline or sorted(available)


def evaluate_legal(
    rulepack: Rulepack,
    variant: Variant,
    staleness_policy: StalenessPolicy,
) -> LegalResult:
    legal = variant.legal
    legal_gate = _normalized_legal_gate(legal.get("legal_gate") or legal.get("gate") or "ok")
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
        invalid_severity="warn",
    )
    stale = rulepack_staleness.is_stale or variant_staleness.is_stale
    freshness_unknown = is_freshness_unknown(rulepack_staleness) or is_freshness_unknown(
        variant_staleness
    )
    regulated = bool(variant.regulated_domain) or any(
        tag in rulepack.regulated_domains for tag in variant.tags
    ) or ("regulated" in variant.tags)

    if variant.regulated_domain and legal_gate == "ok":
        legal_gate = "require_check"
        checklist.append("Regulated domain requires manual legal verification.")

    if regulated and (stale or freshness_unknown):
        legal_gate = "require_check"
        if freshness_unknown:
            checklist.append("DATE_INVALID: re-verify laws before launch.")
        else:
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

    compliance_kits = _select_compliance_kits(rulepack, legal_gate, regulated)
    if legal_gate in {"require_check", "registration", "license", "blocked"}:
        checklist.append("Regulatory review required before launch.")

    return LegalResult(
        legal_gate=legal_gate,
        checklist=checklist,
        compliance_kits=compliance_kits,
        applied_rules=applied_rules,
    )
