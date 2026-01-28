from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from money_map.core.load import load_app_data, load_yaml

EXPECTED_SCHEMA_VERSION = "2026-01-27"

REQUIRED_FILES = [
    "meta.yaml",
    "taxonomy.yaml",
    "cells.yaml",
    "variants.yaml",
    "bridges.yaml",
    "rulepacks/DE.yaml",
    "knowledge/skills.yaml",
    "knowledge/assets.yaml",
    "knowledge/constraints.yaml",
    "knowledge/objectives.yaml",
    "knowledge/risks.yaml",
]
OPTIONAL_FILES: list[str] = []


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


def validate_files_exist(data_dir: Path, strict: bool) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals: list[tuple[str, dict]] = []
    warns: list[tuple[str, dict]] = []
    for rel in REQUIRED_FILES:
        path = data_dir / rel
        if not path.exists():
            fatals.append(("validate.missing_file", {"file": rel}))
    for rel in OPTIONAL_FILES:
        path = data_dir / rel
        if not path.exists():
            if strict:
                fatals.append(("validate.optional_missing_file", {"file": rel}))
            else:
                warns.append(("validate.optional_missing_file", {"file": rel}))
    return fatals, warns


def _ensure_keys(
    label: str, item: dict[str, object], required_keys: list[str]
) -> list[tuple[str, dict]]:
    missing = [key for key in required_keys if key not in item]
    if missing:
        return [("validate.missing_key", {"context": label, "keys": ", ".join(missing)})]
    return []


def _validate_lookup_list(
    label: str, items: object, id_key: str, required_keys: list[str]
) -> list[tuple[str, dict]]:
    if not isinstance(items, list):
        return [("validate.invalid_list", {"context": label})]
    fatals: list[tuple[str, dict]] = []
    ids: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            fatals.append(("validate.invalid_entry", {"context": label}))
            continue
        fatals.extend(_ensure_keys(label, item, required_keys))
        value = item.get(id_key)
        if isinstance(value, str):
            ids.append(value)
    if len(ids) != len(set(ids)):
        fatals.append(("validate.duplicate_ids", {"context": label}))
    return fatals


def validate_app_data(
    data_dir: Path, strict: bool = False
) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals, warns = validate_files_exist(data_dir, strict)
    if fatals:
        return fatals, warns

    appdata = load_app_data(data_dir)

    if not appdata.meta.schema_version:
        fatals.append(("validate.schema_version_required", {}))
    elif appdata.meta.schema_version != EXPECTED_SCHEMA_VERSION:
        fatals.append(
            (
                "validate.schema_version_mismatch",
                {"expected": EXPECTED_SCHEMA_VERSION, "actual": appdata.meta.schema_version},
            )
        )

    variant_ids = [variant.variant_id for variant in appdata.variants]
    if len(set(variant_ids)) != len(variant_ids):
        fatals.append(("validate.variant_id_unique", {}))

    taxonomy_ids = {item.taxonomy_id for item in appdata.taxonomy}
    cell_ids = {cell.cell_id for cell in appdata.cells}

    for variant in appdata.variants:
        fatals.extend(
            _ensure_keys(
                f"variant:{variant.variant_id}",
                variant.model_dump() if hasattr(variant, "model_dump") else variant.__dict__,
                [
                    "variant_id",
                    "title_key",
                    "summary_key",
                    "taxonomy_id",
                    "cells",
                    "tags",
                    "review_date",
                ],
            )
        )
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

    bridges = load_yaml(data_dir / "bridges.yaml")
    if isinstance(bridges, list):
        for bridge in bridges:
            if not isinstance(bridge, dict):
                fatals.append(("validate.bridge_invalid", {}))
                continue
            missing = [key for key in ("from_variant_id", "to_variant_id") if key not in bridge]
            if missing:
                fatals.append(
                    ("validate.bridge_missing_keys", {"keys": ", ".join(missing)})
                )
                continue
            if bridge["from_variant_id"] not in variant_ids or bridge["to_variant_id"] not in variant_ids:
                fatals.append(
                    (
                        "validate.bridge_unknown_variant",
                        {"from_id": bridge["from_variant_id"], "to_id": bridge["to_variant_id"]},
                    )
                )
    elif bridges not in (None, {}):
        fatals.append(("validate.invalid_list", {"context": "bridges"}))

    fatals.extend(
        _validate_lookup_list(
            "knowledge.skills",
            load_yaml(data_dir / "knowledge" / "skills.yaml"),
            "skill_id",
            ["skill_id", "title_key"],
        )
    )
    fatals.extend(
        _validate_lookup_list(
            "knowledge.assets",
            load_yaml(data_dir / "knowledge" / "assets.yaml"),
            "asset_id",
            ["asset_id", "title_key"],
        )
    )
    fatals.extend(
        _validate_lookup_list(
            "knowledge.constraints",
            load_yaml(data_dir / "knowledge" / "constraints.yaml"),
            "constraint_id",
            ["constraint_id", "title_key"],
        )
    )
    fatals.extend(
        _validate_lookup_list(
            "knowledge.objectives",
            load_yaml(data_dir / "knowledge" / "objectives.yaml"),
            "objective_id",
            ["objective_id", "title_key"],
        )
    )
    fatals.extend(
        _validate_lookup_list(
            "knowledge.risks",
            load_yaml(data_dir / "knowledge" / "risks.yaml"),
            "risk_id",
            ["risk_id", "title_key", "category"],
        )
    )

    fatals.extend(
        _ensure_keys(
            "rulepack",
            appdata.rulepack.model_dump()
            if hasattr(appdata.rulepack, "model_dump")
            else appdata.rulepack.__dict__,
            ["country_code", "reviewed_at", "rules", "compliance_kits"],
        )
    )

    fatals.extend(
        _ensure_keys(
            "meta",
            appdata.meta.model_dump()
            if hasattr(appdata.meta, "model_dump")
            else appdata.meta.__dict__,
            ["dataset_version", "schema_version", "reviewed_at", "staleness_policy"],
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
