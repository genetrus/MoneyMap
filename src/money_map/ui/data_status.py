"""Helpers for the Data status page."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from money_map.storage.fs import read_mapping


def data_status_visibility(view_mode: str) -> dict[str, bool]:
    mode = str(view_mode or "User")
    is_developer = mode == "Developer"
    return {
        "show_validate_report": True,
        "show_validation_summary": True,
        "show_raw_report_json": is_developer,
        "show_staleness_details": is_developer,
        "show_data_sources": is_developer,
        "show_compact_summary": not is_developer,
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
    for severity, issues in (
        ("FATAL", report.get("fatals", [])),
        ("WARN", report.get("warns", [])),
    ):
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


def derive_registry_metrics(report: dict[str, Any]) -> dict[str, Any]:
    sources = list(report.get("sources", []))
    variant_sources = [src for src in sources if str(src.get("type")) == "variants"]
    variants_count = sum(int(src.get("items", 0) or 0) for src in variant_sources)

    source_staleness = (report.get("staleness") or {}).get("by_source", {})
    stale_sources = [name for name, details in source_staleness.items() if details.get("is_stale")]

    reviewed_dates = [
        str(src.get("reviewed_at", ""))
        for src in sources
        if str(src.get("reviewed_at", "")).strip()
    ]
    oldest_source_reviewed_at = min(reviewed_dates) if reviewed_dates else ""

    return {
        "dataset_reviewed_at": str(report.get("dataset_reviewed_at", "") or ""),
        "rulepack_reviewed_at": str(report.get("reviewed_at", "") or ""),
        "oldest_source_reviewed_at": oldest_source_reviewed_at,
        "variants_count": variants_count,
        "sources_total": len(sources),
        "stale_sources": stale_sources,
    }



def regulated_domain_coverage(variants: list[dict[str, Any]], rulepack_payload: dict[str, Any]) -> dict[str, int]:
    regulated = [v for v in variants if v.get("regulated_domain") not in (None, "")]
    require_check = [
        v
        for v in regulated
        if str(((v.get("legal") or {}).get("legal_gate") or ((v.get("legal") or {}).get("gate")) or "").lower())
        == "require_check"
    ]

    domain_index = rulepack_payload.get("regulated_domains") or {}
    if isinstance(domain_index, list):
        domain_index = {str(item): {"checklist": []} for item in domain_index}
    checklist_covered = 0
    for variant in regulated:
        domain_id = str(variant.get("regulated_domain") or "")
        entry = domain_index.get(domain_id, {}) if isinstance(domain_index, dict) else {}
        checklist = entry.get("checklist", []) if isinstance(entry, dict) else []
        if checklist:
            checklist_covered += 1

    return {
        "variants_with_regulated_domain": len(regulated),
        "variants_require_check": len(require_check),
        "variants_with_checklist_coverage": checklist_covered,
    }

def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return None


def aggregate_pack_metrics(
    *,
    pack_dir: str | Path,
    staleness_policy_days: int,
    now: date | None = None,
) -> dict[str, Any]:
    pack_dir = Path(pack_dir)
    now_date = now or datetime.utcnow().date()

    variants_payload = read_mapping(pack_dir / "variants.seed.yaml")
    bridges_payload = read_mapping(pack_dir / "bridges.seed.yaml")
    routes_payload = read_mapping(pack_dir / "routes.seed.yaml")
    rulepack_payload = read_mapping(pack_dir / "rulepack.yaml")
    meta_payload = read_mapping(pack_dir / "meta.yaml")

    variants = variants_payload.get("variants", [])
    all_cells = [f"{chr(letter)}{row}" for letter in range(ord("A"), ord("P") + 1) for row in range(1, 5)]
    variants_per_cell = Counter(str(item.get("cell_id", "unknown")) for item in variants)
    for cell in all_cells:
        variants_per_cell.setdefault(cell, 0)

    reviewed_sources = {
        "meta.yaml": str(meta_payload.get("reviewed_at", "") or ""),
        "rulepack.yaml": str(rulepack_payload.get("reviewed_at", "") or ""),
    }

    freshness_rows: list[dict[str, str | int | bool]] = []
    oldest_reviewed_at: date | None = None
    for source, raw_reviewed_at in reviewed_sources.items():
        reviewed = _parse_iso_date(raw_reviewed_at)
        if reviewed is None:
            freshness_rows.append(
                {
                    "source": source,
                    "reviewed_at": raw_reviewed_at,
                    "age_days": -1,
                    "is_stale": True,
                }
            )
            continue

        oldest_reviewed_at = (
            reviewed if oldest_reviewed_at is None else min(oldest_reviewed_at, reviewed)
        )
        age_days = max(0, (now_date - reviewed).days)
        freshness_rows.append(
            {
                "source": source,
                "reviewed_at": reviewed.isoformat(),
                "age_days": age_days,
                "is_stale": age_days > staleness_policy_days,
            }
        )

    stale_sources = [str(row["source"]) for row in freshness_rows if bool(row["is_stale"])]
    regulated_metrics = regulated_domain_coverage(variants, rulepack_payload)
    return {
        "variants_total": len(variants),
        "variants_per_cell": [
            {"label": label, "count": count} for label, count in sorted(variants_per_cell.items())
        ],
        "bridges_total": len(bridges_payload.get("bridges", [])),
        "routes_total": len(routes_payload.get("routes", [])),
        "rule_checks_total": len(rulepack_payload.get("rules", [])),
        "oldest_reviewed_at": oldest_reviewed_at.isoformat() if oldest_reviewed_at else "",
        "freshness": freshness_rows,
        "is_stale": bool(stale_sources),
        "stale_sources": stale_sources,
        "regulated_domain_coverage": regulated_metrics,
    }
