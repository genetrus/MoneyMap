"""Validation helpers for datasets."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from money_map.core.model import AppData, DataSourceInfo, ValidationReport
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


def _parse_iso_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


def _source_staleness(source: DataSourceInfo, policy_days: int) -> dict[str, Any]:
    parsed = _parse_iso_date(source.reviewed_at)
    if parsed is None:
        return {
            "reviewed_at": source.reviewed_at,
            "age_days": None,
            "is_stale": False,
            "severity": "unknown",
            "status": "unknown",
        }
    age_days = max(0, (datetime.utcnow() - parsed).days)
    severity = "ok"
    status = "ok"
    if age_days > policy_days:
        severity = "warn"
        status = "warn"
    return {
        "reviewed_at": source.reviewed_at,
        "age_days": age_days,
        "is_stale": age_days > policy_days,
        "severity": severity,
        "status": status,
    }


def _aggregate_source_staleness(by_source: dict[str, dict[str, Any]]) -> dict[str, Any]:
    known = [item for item in by_source.values() if item.get("age_days") is not None]
    if not known:
        return {
            "status": "unknown",
            "severity": "unknown",
            "is_stale": False,
            "critical_source": "",
            "critical_age_days": None,
        }

    critical = max(known, key=lambda item: int(item.get("age_days") or 0))
    for source, details in by_source.items():
        if details is critical:
            critical_source = source
            break
    else:
        critical_source = ""

    age = int(critical.get("age_days") or 0)
    severity = str(critical.get("severity") or "ok")
    status = "ok" if severity == "ok" else "warn"
    return {
        "status": status,
        "severity": severity,
        "is_stale": status != "ok",
        "critical_source": critical_source,
        "critical_age_days": age,
    }


def _dataset_reviewed_at_from_sources(app_data: AppData) -> str:
    for source in app_data.sources:
        if source.type == "meta" and source.notes.get("group") == "core":
            return source.reviewed_at
    return ""


def _dataset_version_from_sources(app_data: AppData) -> str:
    for source in app_data.sources:
        if source.type == "meta" and source.notes.get("group") == "core":
            return app_data.meta.dataset_version
    return app_data.meta.dataset_version


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
            legal_gate = variant.legal.get("legal_gate") or variant.legal.get("gate")
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

            regulated_domain = variant.regulated_domain
            if regulated_domain:
                known_domains = set(app_data.rulepack.regulated_domains or [])
                if regulated_domain not in known_domains:
                    warns.append(
                        _issue(
                            "VARIANT_REGULATED_DOMAIN_UNKNOWN",
                            message=f"Unknown regulated_domain '{regulated_domain}'",
                            source="variants",
                            location=f"variants[{variant.variant_id}].regulated_domain",
                        )
                    )
                if legal_gate == "ok":
                    warns.append(
                        _issue(
                            "VARIANT_REGULATED_DOMAIN_GATE_TOO_WEAK",
                            message=(
                                f"Variant {variant.variant_id} has regulated_domain={regulated_domain} "
                                "but legal_gate=ok"
                            ),
                            source="variants",
                            location=f"variants[{variant.variant_id}].legal.legal_gate",
                            hint="Use require_check or stricter for regulated domains.",
                        )
                    )
                if not list(variant.legal.get("checklist") or []):
                    warns.append(
                        _issue(
                            "VARIANT_REGULATED_DOMAIN_CHECKLIST_EMPTY",
                            source="variants",
                            location=f"variants[{variant.variant_id}].legal.checklist",
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

    source_staleness_by_source = {
        source.source: _source_staleness(source, app_data.meta.staleness_policy.warn_after_days)
        for source in app_data.sources
    }
    source_staleness_aggregated = _aggregate_source_staleness(source_staleness_by_source)

    return ValidationReport(
        status=status,
        fatals=fatals,
        warns=warns,
        dataset_version=_dataset_version_from_sources(app_data),
        reviewed_at=app_data.rulepack.reviewed_at,
        dataset_reviewed_at=_dataset_reviewed_at_from_sources(app_data),
        stale=stale,
        staleness_policy_days=app_data.meta.staleness_policy.warn_after_days,
        generated_at=datetime.utcnow().replace(microsecond=0).isoformat(),
        sources=app_data.sources,
        staleness={
            "rulepack": asdict(rulepack_staleness),
            "variants": variant_staleness_by_id,
            "by_source": source_staleness_by_source,
            "aggregated": source_staleness_aggregated,
        },
    )
