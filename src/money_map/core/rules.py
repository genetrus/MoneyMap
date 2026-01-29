from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from money_map.core.model import ComplianceKit, RulePack, UserProfile, Variant


@dataclass(frozen=True)
class RuleEvaluation:
    required_kits: list[str]
    compliance_checklist: list[str]
    blockers: list[str]
    warnings: list[str]
    applied_rules: list[str]


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _match_conditions(
    applies_if: dict[str, Any],
    profile: UserProfile,
    variant: Variant,
    country_code: str,
) -> bool:
    tags = set(variant.tags)
    tags_any = set(_as_list(applies_if.get("tags_any")))
    tags_all = set(_as_list(applies_if.get("tags_all")))
    countries = set(_as_list(applies_if.get("country_codes")))
    objectives = set(_as_list(applies_if.get("objective_presets")))
    risk = set(_as_list(applies_if.get("risk_tolerance")))
    modes = set(_as_list(applies_if.get("operational_modes")))

    if tags_any and not tags.intersection(tags_any):
        return False
    if tags_all and not tags_all.issubset(tags):
        return False
    if countries and country_code not in countries:
        return False
    if objectives and profile.objective_preset not in objectives:
        return False
    if risk and profile.risk_tolerance not in risk:
        return False
    if modes and variant.feasibility.operational_mode not in modes:
        return False
    return True


def _kits_for_tags(kits: list[ComplianceKit], tags: set[str]) -> list[str]:
    matched: list[str] = []
    for kit in kits:
        if set(kit.applies_to_tags).intersection(tags):
            matched.append(kit.kit_id)
    return matched


def evaluate_rulepack(
    profile: UserProfile,
    variant: Variant,
    rulepack: RulePack,
    today: date | None = None,
) -> RuleEvaluation:
    _ = today or date.today()
    required_kits = _as_list(variant.legal.required_kits)
    required_kits.extend(_kits_for_tags(rulepack.compliance_kits, set(variant.tags)))

    blockers: list[str] = []
    warnings: list[str] = []
    checklist_items: list[str] = []
    applied_rules: list[str] = []

    for rule in rulepack.rules:
        applies_if = rule.applies_if if isinstance(rule.applies_if, dict) else {}
        if not _match_conditions(applies_if, profile, variant, rulepack.country_code):
            continue
        effects = rule.effects if isinstance(rule.effects, dict) else {}
        required_kits.extend(_as_list(effects.get("add_kits")))
        blockers.extend(_as_list(effects.get("add_blockers")))
        warnings.extend(_as_list(effects.get("add_warnings")))
        checklist_items.extend(_as_list(effects.get("add_checklist")))
        applied_rules.append(rule.rule_id)

    kits_by_id = {kit.kit_id: kit for kit in rulepack.compliance_kits}
    for kit_id in required_kits:
        kit = kits_by_id.get(kit_id)
        if kit:
            checklist_items.extend(_as_list(kit.checklist))

    return RuleEvaluation(
        required_kits=_dedupe_keep_order(required_kits),
        compliance_checklist=_dedupe_keep_order(checklist_items),
        blockers=_dedupe_keep_order(blockers),
        warnings=_dedupe_keep_order(warnings),
        applied_rules=_dedupe_keep_order(applied_rules),
    )
