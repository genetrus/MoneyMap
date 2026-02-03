"""Validation helpers for datasets."""

from __future__ import annotations

from dataclasses import asdict

from money_map.core.model import AppData, ValidationReport
from money_map.core.staleness import evaluate_staleness


def validate(app_data: AppData) -> ValidationReport:
    fatals: list[str] = []
    warns: list[str] = []

    if not app_data.meta.dataset_version:
        fatals.append("META_DATASET_VERSION_MISSING")

    reviewed_at = app_data.rulepack.reviewed_at
    rulepack_staleness = evaluate_staleness(
        reviewed_at,
        app_data.meta.staleness_policy,
        label="rulepack",
    )
    if rulepack_staleness.severity == "fatal":
        fatals.append("RULEPACK_REVIEWED_AT_INVALID")

    if not app_data.rulepack.rules:
        warns.append("RULEPACK_RULES_EMPTY")

    if not app_data.variants:
        fatals.append("VARIANTS_EMPTY")

    stale_variants: list[str] = []
    variant_staleness_by_id: dict[str, dict] = {}
    for variant in app_data.variants:
        if not variant.variant_id:
            fatals.append("VARIANT_ID_MISSING")
        if not variant.title:
            fatals.append(f"VARIANT_TITLE_MISSING:{variant.variant_id}")
        if not variant.summary:
            warns.append(f"VARIANT_SUMMARY_MISSING:{variant.variant_id}")
        if not variant.economics:
            warns.append(f"VARIANT_ECONOMICS_MISSING:{variant.variant_id}")
        if not variant.legal:
            warns.append(f"VARIANT_LEGAL_MISSING:{variant.variant_id}")
        variant_staleness = evaluate_staleness(
            variant.review_date,
            app_data.meta.staleness_policy,
            label=f"variant:{variant.variant_id}",
        )
        if variant_staleness.is_stale:
            stale_variants.append(variant.variant_id)
        variant_staleness_by_id[variant.variant_id] = asdict(variant_staleness)

    stale = False
    if rulepack_staleness.is_stale:
        stale = True
        warns.append("STALE_RULEPACK")
    if stale_variants:
        warns.append(f"STALE_VARIANTS:{', '.join(sorted(stale_variants))}")

    status = "invalid" if fatals else "valid"
    return ValidationReport(
        status=status,
        fatals=fatals,
        warns=warns,
        dataset_version=app_data.meta.dataset_version,
        reviewed_at=app_data.rulepack.reviewed_at,
        stale=stale,
        staleness={
            "rulepack": asdict(rulepack_staleness),
            "variants": variant_staleness_by_id,
        },
    )
