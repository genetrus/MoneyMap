"""Helpers for the Data status page."""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable


def data_status_visibility(view_mode: str) -> dict[str, bool]:
    return {
        "show_validate_report": True,
        "show_validation_summary": True,
        "show_raw_report_json": True,
        "show_staleness_details": True,
        "show_data_sources": True,
    }


def user_alert_for_status(status: str) -> tuple[str, str] | None:
    if status == "invalid":
        return (
            "error",
            "**Data is invalid**\n\n"
            "Some required data checks failed. Results may be unreliable.\n\n"
            "Switch to Developer mode for details.",
        )
    if status == "stale":
        return (
            "warning",
            "**Data is stale**\n\n"
            "The dataset review date is older than the staleness policy. Results may be "
            "cautious.\n\n"
            "Switch to Developer mode for details.",
        )
    return None


def build_validate_rows(report: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for severity, issues in (("FATAL", report.get("fatals", [])), ("WARN", report.get("warns", []))):
        for issue in issues:
            entity_type = str(issue.get("source") or "unknown")
            rows.append(
                {
                    "severity": severity,
                    "entity_type": entity_type,
                    "entity_id": str(issue.get("location") or ""),
                    "message": str(issue.get("message") or ""),
                    "code": str(issue.get("code") or ""),
                }
            )
    return rows


def filter_validate_rows(
    rows: list[dict[str, str]], *, severity: str = "ALL", entity_type: str = "ALL"
) -> list[dict[str, str]]:
    out = rows
    if severity != "ALL":
        out = [row for row in out if row["severity"] == severity]
    if entity_type != "ALL":
        out = [row for row in out if row["entity_type"] == entity_type]
    return out


def variants_by_cell(
    variants: list[Any],
    *,
    cell_resolver: Callable[[Any], str],
) -> list[dict[str, int | str]]:
    counts: Counter[str] = Counter(cell_resolver(variant) for variant in variants)
    return [{"label": label, "count": count} for label, count in sorted(counts.items())]


def variants_by_legal_gate(variants: list[Any]) -> list[dict[str, int | str]]:
    counts: Counter[str] = Counter(
        str((variant.legal or {}).get("legal_gate", "unknown")) for variant in variants
    )
    return [{"label": label, "count": count} for label, count in sorted(counts.items())]


def oldest_stale_entities(
    variant_staleness: dict[str, dict[str, Any]],
    *,
    limit: int = 10,
) -> list[dict[str, int | str]]:
    rows = []
    for variant_id, details in variant_staleness.items():
        age_days = details.get("age_days")
        if age_days is None:
            continue
        rows.append(
            {
                "variant_id": variant_id,
                "age_days": int(age_days),
                "severity": str(details.get("severity", "")),
                "is_stale": str(details.get("is_stale", False)),
            }
        )

    rows.sort(key=lambda item: int(item["age_days"]), reverse=True)
    return rows[:limit]
