from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from money_map.core.load import load_app_data

REQUIRED_FILES = [
    "meta.yaml",
    "taxonomy.yaml",
    "cells.yaml",
    "variants.yaml",
    "bridges.yaml",
    "rulepacks/DE.yaml",
]


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


def validate_files_exist(data_dir: Path) -> list[tuple[str, dict]]:
    fatals: list[tuple[str, dict]] = []
    for rel in REQUIRED_FILES:
        path = data_dir / rel
        if not path.exists():
            fatals.append(("validate.missing_file", {"file": rel}))
    return fatals


def validate_app_data(data_dir: Path) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals = validate_files_exist(data_dir)
    warns: list[tuple[str, dict]] = []
    if fatals:
        return fatals, warns

    appdata = load_app_data(data_dir)

    if not appdata.meta.schema_version:
        fatals.append(("validate.schema_version_required", {}))

    variant_ids = [variant.variant_id for variant in appdata.variants]
    if len(set(variant_ids)) != len(variant_ids):
        fatals.append(("validate.variant_id_unique", {}))

    taxonomy_ids = {item.taxonomy_id for item in appdata.taxonomy}
    cell_ids = {cell.cell_id for cell in appdata.cells}

    for variant in appdata.variants:
        if variant.taxonomy_id not in taxonomy_ids:
            fatals.append(
                (
                    "validate.unknown_taxonomy_id",
                    {"variant_id": variant.variant_id},
                )
            )
        missing_cells = [cell for cell in variant.cells if cell not in cell_ids]
        if missing_cells:
            fatals.append(
                (
                    "validate.unknown_cell_ids",
                    {
                        "variant_id": variant.variant_id,
                        "cell_ids": ", ".join(missing_cells),
                    },
                )
            )

    today = date.today()
    meta_reviewed = _to_date(appdata.meta.reviewed_at)
    days_since_meta = (today - meta_reviewed).days
    policy = appdata.meta.staleness_policy
    if days_since_meta > policy.warn_after_days:
        warns.append(("validate.dataset_stale", {"days": days_since_meta}))

    rulepack_reviewed = _to_date(appdata.rulepack.reviewed_at)
    days_since_rulepack = (today - rulepack_reviewed).days
    if days_since_rulepack > policy.warn_after_days:
        warns.append(("validate.rulepack_stale", {"days": days_since_rulepack}))

    regulated_tags = set(policy.regulated_tags)
    require_check_stale = (
        days_since_meta > policy.force_require_check_after_days
        or days_since_rulepack > policy.force_require_check_after_days
    )
    if require_check_stale:
        for variant in appdata.variants:
            if regulated_tags.intersection(variant.tags):
                warns.append(
                    (
                        "validate.regulated_requires_check",
                        {"variant_id": variant.variant_id},
                    )
                )

    return fatals, warns
