"""Validation helpers for datasets."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from money_map.core.model import AppData, ValidationReport
from money_map.core.staleness import evaluate_staleness


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
    if rulepack_staleness.severity == "fatal":
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
    for variant in app_data.variants:
        if not variant.variant_id:
            fatals.append(
                _issue(
                    "VARIANT_ID_MISSING",
                    source="variants",
                    location="variants[].variant_id",
                )
            )
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
        if not variant.economics:
            warns.append(
                _issue(
                    "VARIANT_ECONOMICS_MISSING",
                    message=f"Variant economics missing for {variant.variant_id}",
                    source="variants",
                    location=f"variants[{variant.variant_id}].economics",
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
                "STALE_RULEPACK",
                message="Rulepack is stale.",
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
        staleness_policy_days=app_data.meta.staleness_policy.stale_after_days,
        generated_at=datetime.utcnow().replace(microsecond=0).isoformat(),
        staleness={
            "rulepack": asdict(rulepack_staleness),
            "variants": variant_staleness_by_id,
        },
    )
