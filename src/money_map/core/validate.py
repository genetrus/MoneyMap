"""Validation helpers for datasets."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from money_map.core.model import AppData, ValidationReport

_DATE_FORMATS = ["%Y-%m-%d"]


def _parse_date(value: str) -> date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def validate(app_data: AppData) -> ValidationReport:
    fatals: list[str] = []
    warns: list[str] = []

    if not app_data.meta.dataset_version:
        fatals.append("META_DATASET_VERSION_MISSING")

    reviewed_at = app_data.rulepack.reviewed_at
    reviewed_date = _parse_date(reviewed_at)
    if not reviewed_date:
        fatals.append("RULEPACK_REVIEWED_AT_INVALID")

    if not app_data.rulepack.rules:
        warns.append("RULEPACK_RULES_EMPTY")

    if not app_data.variants:
        fatals.append("VARIANTS_EMPTY")

    stale_variants: list[str] = []
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
        review_date = _parse_date(variant.review_date)
        if review_date:
            stale_after = timedelta(days=app_data.meta.staleness_policy.stale_after_days)
            if date.today() - review_date > stale_after:
                stale_variants.append(variant.variant_id)

    stale = False
    if reviewed_date:
        stale_after = timedelta(days=app_data.rulepack.staleness_policy.stale_after_days)
        stale = date.today() - reviewed_date > stale_after
        if stale:
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
    )
