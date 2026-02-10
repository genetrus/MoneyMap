"""Validation helpers for datasets."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from money_map.core.model import AppData, ValidationReport
from money_map.core.staleness import evaluate_staleness

ALLOWED_LEGAL_GATES = {"ok", "require_check", "registration", "license", "blocked"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}


def _issue(
    code: str,
    *,
    message: str | None = None,
    source: str | None = None,
    location: str | None = None,
    hint: str | None = None,
) -> dict[str, str]:
    return {
        "code": code,
        "message": message or code,
        "source": source or "",
        "location": location or "",
        "hint": hint or "",
    }


def _is_range(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(v, (int, float)) for v in value)
    )


def _validate_numeric_range(
    value: Any,
    *,
    source: str,
    location: str,
    code: str,
    warns: list[dict[str, str]],
) -> None:
    if not _is_range(value):
        warns.append(
            _issue(
                code,
                source=source,
                location=location,
                hint="Expected numeric range [min, max].",
            )
        )
        return
    if value[0] > value[1]:
        warns.append(
            _issue(
                f"{code}_ORDER",
                source=source,
                location=location,
                hint="Range min must be <= max.",
            )
        )


def validate(app_data: AppData) -> ValidationReport:
    fatals: list[dict[str, str]] = []
    warns: list[dict[str, str]] = []

    if not app_data.meta.dataset_version:
        fatals.append(
            _issue(
                "META_DATASET_VERSION_MISSING",
                source="meta",
                location="meta.dataset_version",
            )
        )

    reviewed_at = app_data.rulepack.reviewed_at
    rulepack_staleness = evaluate_staleness(
        reviewed_at,
        app_data.meta.staleness_policy,
        label="rulepack",
    )
    if rulepack_staleness.age_days is None and rulepack_staleness.severity == "fatal":
        fatals.append(
            _issue(
                "RULEPACK_REVIEWED_AT_INVALID",
                source="rulepack",
                location="rulepack.reviewed_at",
            )
        )

    if not app_data.rulepack.rules:
        warns.append(
            _issue(
                "RULEPACK_RULES_EMPTY",
                source="rulepack",
                location="rulepack.rules",
            )
        )

    known_rule_ids: set[str] = set()
    for idx, rule in enumerate(app_data.rulepack.rules):
        if not rule.rule_id:
            fatals.append(
                _issue(
                    "RULEPACK_RULE_ID_MISSING",
                    source="rulepack",
                    location=f"rulepack.rules[{idx}].rule_id",
                )
            )
            continue
        if rule.rule_id in known_rule_ids:
            fatals.append(
                _issue(
                    "RULEPACK_RULE_ID_DUPLICATE",
                    message=f"Duplicate rule_id in rulepack: {rule.rule_id}",
                    source="rulepack",
                    location=f"rulepack.rules[{idx}].rule_id",
                )
            )
        known_rule_ids.add(rule.rule_id)

    if not app_data.variants:
        fatals.append(
            _issue(
                "VARIANTS_EMPTY",
                source="variants",
                location="variants",
            )
        )

    stale_variants: list[str] = []
    variant_staleness_by_id: dict[str, dict] = {}
    known_variant_ids: set[str] = set()

    for variant in app_data.variants:
        if not variant.variant_id:
            fatals.append(
                _issue(
                    "VARIANT_ID_MISSING",
                    source="variants",
                    location="variants[].variant_id",
                )
            )
        elif variant.variant_id in known_variant_ids:
            fatals.append(
                _issue(
                    "VARIANT_ID_DUPLICATE",
                    message=f"Duplicate variant_id: {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].variant_id",
                )
            )
        known_variant_ids.add(variant.variant_id)

        if not variant.title:
            fatals.append(
                _issue(
                    "VARIANT_TITLE_MISSING",
                    message=f"Variant title missing for {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].title",
                )
            )
        if not variant.summary:
            warns.append(
                _issue(
                    "VARIANT_SUMMARY_MISSING",
                    message=f"Variant summary missing for {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].summary",
                )
            )

        if not variant.prep_steps:
            warns.append(
                _issue(
                    "VARIANT_PREP_STEPS_EMPTY",
                    source="variants",
                    location=f"variants[{variant.variant_id}].prep_steps",
                )
            )

        if not variant.economics:
            warns.append(
                _issue(
                    "VARIANT_ECONOMICS_MISSING",
                    message=f"Variant economics missing for {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].economics",
                )
            )
        else:
            _validate_numeric_range(
                variant.economics.get("time_to_first_money_days_range"),
                source="variants",
                location=f"variants[{variant.variant_id}].economics.time_to_first_money_days_range",
                code="VARIANT_ECONOMICS_TIME_RANGE_INVALID",
                warns=warns,
            )
            _validate_numeric_range(
                variant.economics.get("typical_net_month_eur_range"),
                source="variants",
                location=f"variants[{variant.variant_id}].economics.typical_net_month_eur_range",
                code="VARIANT_ECONOMICS_NET_RANGE_INVALID",
                warns=warns,
            )
            _validate_numeric_range(
                variant.economics.get("costs_eur_range"),
                source="variants",
                location=f"variants[{variant.variant_id}].economics.costs_eur_range",
                code="VARIANT_ECONOMICS_COST_RANGE_INVALID",
                warns=warns,
            )
            confidence = variant.economics.get("confidence")
            if confidence and confidence not in ALLOWED_CONFIDENCE:
                warns.append(
                    _issue(
                        "VARIANT_ECONOMICS_CONFIDENCE_UNKNOWN",
                        message=f"Unknown confidence enum: {confidence}",
                        source="variants",
                        location=f"variants[{variant.variant_id}].economics.confidence",
                        hint="Use one of: low, medium, high.",
                    )
                )

        if not variant.legal:
            warns.append(
                _issue(
                    "VARIANT_LEGAL_MISSING",
                    message=f"Variant legal missing for {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].legal",
                )
            )
        else:
            legal_gate = variant.legal.get("legal_gate")
            if not legal_gate:
                warns.append(
                    _issue(
                        "VARIANT_LEGAL_GATE_MISSING",
                        source="variants",
                        location=f"variants[{variant.variant_id}].legal.legal_gate",
                    )
                )
            elif legal_gate not in ALLOWED_LEGAL_GATES:
                warns.append(
                    _issue(
                        "VARIANT_LEGAL_GATE_UNKNOWN",
                        message=f"Unknown legal gate enum: {legal_gate}",
                        source="variants",
                        location=f"variants[{variant.variant_id}].legal.legal_gate",
                        hint="Use one of: ok, require_check, registration, license, blocked.",
                    )
                )

            referenced_rules = variant.legal.get("rule_ids", [])
            if isinstance(referenced_rules, list):
                for idx, rule_id in enumerate(referenced_rules):
                    if rule_id not in known_rule_ids:
                        warns.append(
                            _issue(
                                "VARIANT_RULE_REF_UNKNOWN",
                                message=(
                                    f"Unknown rule reference '{rule_id}' in {variant.variant_id}"
                                ),
                                source="variants",
                                location=f"variants[{variant.variant_id}].legal.rule_ids[{idx}]",
                            )
                        )

        feasibility = variant.feasibility or {}
        for key in ("min_capital", "min_time_per_week"):
            value = feasibility.get(key)
            if value is not None and isinstance(value, (int, float)) and value < 0:
                warns.append(
                    _issue(
                        "VARIANT_FEASIBILITY_NEGATIVE_VALUE",
                        message=f"{key} cannot be negative for {variant.variant_id}",
                        source="variants",
                        location=f"variants[{variant.variant_id}].feasibility.{key}",
                    )
                )

        variant_staleness = evaluate_staleness(
            variant.review_date,
            app_data.meta.staleness_policy,
            label=f"variant:{variant.variant_id}",
            invalid_severity="warn",
        )
        if variant_staleness.age_days is None:
            warns.append(
                _issue(
                    "VARIANT_REVIEW_DATE_INVALID",
                    message=f"Variant review date invalid for {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].review_date",
                )
            )
        if variant_staleness.is_stale:
            stale_variants.append(variant.variant_id)
        variant_staleness_by_id[variant.variant_id] = asdict(variant_staleness)

    stale = False
    if rulepack_staleness.is_stale:
        stale = True
        warns.append(
            _issue(
                "STALE_RULEPACK_HARD" if rulepack_staleness.is_hard_stale else "STALE_RULEPACK",
                message=(
                    "Rulepack is hard-stale."
                    if rulepack_staleness.is_hard_stale
                    else "Rulepack is stale."
                ),
                source="rulepack",
                location="rulepack.reviewed_at",
            )
        )
    if stale_variants:
        warns.append(
            _issue(
                "STALE_VARIANTS",
                message=f"Stale variants: {', '.join(sorted(stale_variants))}",
                source="variants",
                location="variants[].review_date",
            )
        )

    if fatals:
        status = "invalid"
    elif stale:
        status = "stale"
    else:
        status = "valid"

    return ValidationReport(
        status=status,
        fatals=fatals,
        warns=warns,
        dataset_version=app_data.meta.dataset_version,
        reviewed_at=app_data.rulepack.reviewed_at,
        stale=stale,
        staleness_policy_days=app_data.meta.staleness_policy.warn_after_days,
        generated_at=datetime.utcnow().replace(microsecond=0).isoformat(),
        staleness={
            "rulepack": asdict(rulepack_staleness),
            "variants": variant_staleness_by_id,
        },
    )
