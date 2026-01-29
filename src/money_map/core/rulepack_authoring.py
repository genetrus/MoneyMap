from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from money_map.core.yaml_utils import dump_yaml


DEFAULT_PLACEHOLDER_NOTICE_KEY = "rulepack.placeholder.notice"


@dataclass(frozen=True)
class RulepackIssue:
    key: str
    params: dict[str, Any]


def scaffold_kit(
    kit_id: str, title_key: str, summary_key: str, regulated_level: str
) -> dict[str, Any]:
    return {
        "kit_id": kit_id,
        "title_key": title_key,
        "summary_key": summary_key,
        "regulated_level": regulated_level,
        "checklist": [],
        "applies_to_tags": [],
    }


def _placeholder_kit_specs(country_code: str) -> list[dict[str, Any]]:
    prefix = country_code.lower()
    return [
        scaffold_kit(
            f"{prefix}.registration",
            f"kit.{prefix}.registration.title",
            f"kit.{prefix}.registration.summary",
            "light",
        ),
        scaffold_kit(
            f"{prefix}.invoicing",
            f"kit.{prefix}.invoicing.title",
            f"kit.{prefix}.invoicing.summary",
            "light",
        ),
        scaffold_kit(
            f"{prefix}.taxes",
            f"kit.{prefix}.taxes.title",
            f"kit.{prefix}.taxes.summary",
            "medium",
        ),
        scaffold_kit(
            f"{prefix}.insurance",
            f"kit.{prefix}.insurance.title",
            f"kit.{prefix}.insurance.summary",
            "light",
        ),
        scaffold_kit(
            f"{prefix}.safety",
            f"kit.{prefix}.safety.title",
            f"kit.{prefix}.safety.summary",
            "medium",
        ),
        scaffold_kit(
            f"{prefix}.permits",
            f"kit.{prefix}.permits.title",
            f"kit.{prefix}.permits.summary",
            "medium",
        ),
        scaffold_kit(
            f"{prefix}.data_protection",
            f"kit.{prefix}.data_protection.title",
            f"kit.{prefix}.data_protection.summary",
            "medium",
        ),
        scaffold_kit(
            f"{prefix}.employment",
            f"kit.{prefix}.employment.title",
            f"kit.{prefix}.employment.summary",
            "medium",
        ),
    ]


def scaffold_rulepack(
    country_code: str, out_path: Path, placeholder: bool = True
) -> dict[str, Any]:
    country_code = country_code.upper()
    rulepack: dict[str, Any] = {
        "country_code": country_code,
        "reviewed_at": date.today().isoformat(),
        "rules": [],
        "compliance_kits": [],
    }
    if placeholder:
        rulepack.update(
            {
                "is_placeholder": True,
                "placeholder_notice_key": DEFAULT_PLACEHOLDER_NOTICE_KEY,
            }
        )
        prefix = country_code.lower()
        rulepack["rules"] = [
            {
                "rule_id": f"{prefix}.regulated.verify",
                "title_key": f"rule.{prefix}.regulated.title",
                "summary_key": f"rule.{prefix}.regulated.summary",
                "applies_if": {"tags_any": ["regulated", "finance", "health"]},
                "effects": {
                    "add_blockers": ["reason.review.requires_verification"],
                    "add_checklist": [
                        f"rulepack.{prefix}.verify.registration",
                        f"rulepack.{prefix}.verify.taxes",
                    ],
                },
            }
        ]
        rulepack["compliance_kits"] = _placeholder_kit_specs(country_code)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(dump_yaml(rulepack), encoding="utf-8")
    return rulepack


def validate_rulepack_structure(rulepack: Any) -> list[RulepackIssue]:
    issues: list[RulepackIssue] = []
    if not isinstance(rulepack, dict):
        return [RulepackIssue("rulepack.invalid_format", {})]

    required_keys = ["country_code", "reviewed_at", "rules", "compliance_kits"]
    missing = [key for key in required_keys if key not in rulepack]
    if missing:
        issues.append(
            RulepackIssue("rulepack.missing_keys", {"keys": ", ".join(missing)})
        )
        return issues

    if rulepack.get("is_placeholder") and not rulepack.get("placeholder_notice_key"):
        issues.append(RulepackIssue("rulepack.placeholder_missing_notice", {}))

    rules = rulepack.get("rules")
    kits = rulepack.get("compliance_kits")
    if not isinstance(rules, list):
        issues.append(RulepackIssue("rulepack.invalid_rules", {}))
        rules = []
    if not isinstance(kits, list):
        issues.append(RulepackIssue("rulepack.invalid_kits", {}))
        kits = []

    rule_ids: list[str] = []
    kit_ids: list[str] = []

    for rule in rules:
        if not isinstance(rule, dict):
            issues.append(RulepackIssue("rulepack.rule_invalid", {}))
            continue
        for key in ["rule_id", "title_key", "summary_key", "applies_if", "effects"]:
            if key not in rule:
                issues.append(
                    RulepackIssue(
                        "rulepack.rule_missing_key",
                        {"rule_id": rule.get("rule_id", ""), "key": key},
                    )
                )
        rule_id = rule.get("rule_id")
        if isinstance(rule_id, str):
            rule_ids.append(rule_id)

    for kit in kits:
        if not isinstance(kit, dict):
            issues.append(RulepackIssue("rulepack.kit_invalid", {}))
            continue
        for key in [
            "kit_id",
            "title_key",
            "summary_key",
            "regulated_level",
            "checklist",
            "applies_to_tags",
        ]:
            if key not in kit:
                issues.append(
                    RulepackIssue(
                        "rulepack.kit_missing_key",
                        {"kit_id": kit.get("kit_id", ""), "key": key},
                    )
                )
        kit_id = kit.get("kit_id")
        if isinstance(kit_id, str):
            kit_ids.append(kit_id)

    if len(rule_ids) != len(set(rule_ids)):
        issues.append(RulepackIssue("rulepack.rule_ids_duplicate", {}))
    if len(kit_ids) != len(set(kit_ids)):
        issues.append(RulepackIssue("rulepack.kit_ids_duplicate", {}))

    kit_ids_set = set(kit_ids)
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        effects = rule.get("effects") if isinstance(rule.get("effects"), dict) else {}
        for kit_id in effects.get("add_kits", []) or []:
            if kit_id not in kit_ids_set:
                issues.append(
                    RulepackIssue(
                        "rulepack.rule_unknown_kit",
                        {"rule_id": rule.get("rule_id", ""), "kit_id": kit_id},
                    )
                )

    return issues


def lint_rulepack(rulepack: Any) -> list[RulepackIssue]:
    warnings: list[RulepackIssue] = []
    if not isinstance(rulepack, dict):
        return [RulepackIssue("rulepack.invalid_format", {})]

    rules = rulepack.get("rules") if isinstance(rulepack.get("rules"), list) else []
    kits = (
        rulepack.get("compliance_kits")
        if isinstance(rulepack.get("compliance_kits"), list)
        else []
    )

    referenced_kits: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        effects = rule.get("effects") if isinstance(rule.get("effects"), dict) else {}
        for kit_id in effects.get("add_kits", []) or []:
            referenced_kits.add(kit_id)
        applies_if = rule.get("applies_if") if isinstance(rule.get("applies_if"), dict) else {}
        if not applies_if:
            warnings.append(
                RulepackIssue(
                    "rulepack.lint.rule_missing_conditions",
                    {"rule_id": rule.get("rule_id", "")},
                )
            )
        if not effects:
            warnings.append(
                RulepackIssue(
                    "rulepack.lint.rule_missing_effects",
                    {"rule_id": rule.get("rule_id", "")},
                )
            )

    for kit in kits:
        if not isinstance(kit, dict):
            continue
        kit_id = kit.get("kit_id", "")
        tags = kit.get("applies_to_tags") if isinstance(kit.get("applies_to_tags"), list) else []
        if kit_id and kit_id not in referenced_kits and not tags:
            warnings.append(
                RulepackIssue(
                    "rulepack.lint.unused_kit",
                    {"kit_id": kit_id},
                )
            )
        if len(tags) != len(set(tags)):
            warnings.append(
                RulepackIssue(
                    "rulepack.lint.duplicate_tags",
                    {"kit_id": kit_id},
                )
            )

    return warnings
