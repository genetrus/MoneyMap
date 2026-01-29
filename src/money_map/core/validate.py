from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from money_map.core.evidence import validate_registry
from money_map.core.load import load_app_data, load_yaml
from money_map.core.reviews import validate_reviews_data
from money_map.core.workspace import get_workspace_paths
from money_map.core.schema_version import EXPECTED_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS
from money_map.i18n.i18n import load_lang

REQUIRED_FILES = [
    "meta.yaml",
    "taxonomy.yaml",
    "cells.yaml",
    "variants.yaml",
    "bridges.yaml",
    "presets.yaml",
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


def _parse_date(value: date | str) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def validate_files_exist(
    data_dir: Path, strict: bool
) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
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
    data_dir: Path, strict: bool = False, workspace: Path | None = None
) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals, warns = validate_files_exist(data_dir, strict)
    if fatals:
        return fatals, warns

    appdata = load_app_data(data_dir, workspace=workspace)

    if not appdata.meta.schema_version:
        fatals.append(("validate.schema_version_required", {}))
    elif appdata.meta.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        fatals.append(
            (
                "validate.schema_version_mismatch",
                {"expected": EXPECTED_SCHEMA_VERSION, "actual": appdata.meta.schema_version},
            )
        )
    if not appdata.meta.dataset_version:
        fatals.append(("validate.dataset_version_required", {}))
    if _parse_date(appdata.meta.reviewed_at) is None:
        fatals.append(("validate.invalid_date", {"context": "meta.reviewed_at"}))

    variant_ids = [variant.variant_id for variant in appdata.variants]
    if len(set(variant_ids)) != len(variant_ids):
        fatals.append(("validate.variant_id_unique", {}))

    taxonomy_ids = {item.taxonomy_id for item in appdata.taxonomy}
    cell_ids = {cell.cell_id for cell in appdata.cells}
    skill_ids = {item.skill_id for item in appdata.skills}
    asset_ids = {item.asset_id for item in appdata.assets}
    constraint_ids = {item.constraint_id for item in appdata.constraints}
    objective_ids = {item.objective_id for item in appdata.objectives}
    risk_ids = {item.risk_id for item in appdata.risks}
    preset_ids = [item.preset_id for item in appdata.presets]
    if len(set(preset_ids)) != len(preset_ids):
        fatals.append(("validate.preset_id_unique", {}))

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
                    "feasibility",
                    "economics",
                    "legal",
                    "evidence",
                    "required_skills",
                    "required_assets",
                    "constraints",
                    "objectives",
                    "risks",
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
        if _parse_date(variant.review_date) is None:
            fatals.append(
                ("validate.invalid_date", {"context": f"variant:{variant.variant_id}.review_date"})
            )
        missing_skills = [item for item in variant.required_skills if item not in skill_ids]
        if missing_skills:
            fatals.append(
                (
                    "validate.unknown_skill_ids",
                    {"variant_id": variant.variant_id, "skill_ids": ", ".join(missing_skills)},
                )
            )
        missing_assets = [item for item in variant.required_assets if item not in asset_ids]
        if missing_assets:
            fatals.append(
                (
                    "validate.unknown_asset_ids",
                    {"variant_id": variant.variant_id, "asset_ids": ", ".join(missing_assets)},
                )
            )
        missing_constraints = [
            item for item in variant.constraints if item not in constraint_ids
        ]
        if missing_constraints:
            fatals.append(
                (
                    "validate.unknown_constraint_ids",
                    {
                        "variant_id": variant.variant_id,
                        "constraint_ids": ", ".join(missing_constraints),
                    },
                )
            )
        missing_objectives = [
            item for item in variant.objectives if item not in objective_ids
        ]
        if missing_objectives:
            fatals.append(
                (
                    "validate.unknown_objective_ids",
                    {
                        "variant_id": variant.variant_id,
                        "objective_ids": ", ".join(missing_objectives),
                    },
                )
            )
        missing_risks = [item for item in variant.risks if item not in risk_ids]
        if missing_risks:
            fatals.append(
                (
                    "validate.unknown_risk_ids",
                    {"variant_id": variant.variant_id, "risk_ids": ", ".join(missing_risks)},
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
            if (
                bridge["from_variant_id"] not in variant_ids
                or bridge["to_variant_id"] not in variant_ids
            ):
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
            "presets",
            load_yaml(data_dir / "presets.yaml"),
            "preset_id",
            [
                "preset_id",
                "title_key",
                "summary_key",
                "weight_feasibility",
                "weight_economics",
                "weight_legal",
                "weight_fit",
                "weight_staleness",
            ],
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

    for country_code, rulepack in appdata.rulepacks.items():
        fatals.extend(
            _ensure_keys(
                f"rulepack:{country_code}",
                rulepack.model_dump()
                if hasattr(rulepack, "model_dump")
                else rulepack.__dict__,
                ["country_code", "reviewed_at", "rules", "compliance_kits"],
            )
        )
        rules_payload = [
            rule.model_dump() if hasattr(rule, "model_dump") else rule.__dict__
            for rule in rulepack.rules
        ]
        kits_payload = [
            kit.model_dump() if hasattr(kit, "model_dump") else kit.__dict__
            for kit in rulepack.compliance_kits
        ]
        fatals.extend(
            _validate_lookup_list(
                f"rulepack:{country_code}.rules",
                rules_payload,
                "rule_id",
                ["rule_id", "title_key", "summary_key", "applies_if", "effects"],
            )
        )
        fatals.extend(
            _validate_lookup_list(
                f"rulepack:{country_code}.compliance_kits",
                kits_payload,
                "kit_id",
                [
                    "kit_id",
                    "title_key",
                    "summary_key",
                    "regulated_level",
                    "checklist",
                    "applies_to_tags",
                ],
            )
        )
        if _parse_date(rulepack.reviewed_at) is None:
            fatals.append(
                ("validate.invalid_date", {"context": f"rulepack:{country_code}.reviewed_at"})
            )
        if rulepack.country_code != country_code:
            fatals.append(
                ("validate.rulepack_country_mismatch", {"country_code": country_code})
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

    if appdata.meta.supported_countries:
        missing_rulepacks = [
            code for code in appdata.meta.supported_countries if code not in appdata.rulepacks
        ]
        if missing_rulepacks:
            fatals.append(
                ("validate.missing_rulepack", {"country_codes": ", ".join(missing_rulepacks)})
            )

    en_translations = load_lang("en")
    i18n_keys: set[str] = set()
    for taxonomy in appdata.taxonomy:
        i18n_keys.add(taxonomy.title_key)
    for cell in appdata.cells:
        i18n_keys.add(cell.title_key)
    for variant in appdata.variants:
        i18n_keys.add(variant.title_key)
        i18n_keys.add(variant.summary_key)
        econ = variant.economics
        if isinstance(econ, dict):
            margin_key = econ.get("margin_notes_key")
        else:
            margin_key = econ.margin_notes_key if econ else None
        if margin_key:
            i18n_keys.add(margin_key)
        legal = variant.legal
        if isinstance(legal, dict):
            disclaimer_key = legal.get("disclaimers_key")
        else:
            disclaimer_key = legal.disclaimers_key if legal else None
        if disclaimer_key:
            i18n_keys.add(disclaimer_key)
    for item in appdata.skills:
        i18n_keys.add(item.title_key)
    for item in appdata.assets:
        i18n_keys.add(item.title_key)
    for item in appdata.constraints:
        i18n_keys.add(item.title_key)
    for item in appdata.objectives:
        i18n_keys.add(item.title_key)
    for preset in appdata.presets:
        i18n_keys.add(preset.title_key)
        i18n_keys.add(preset.summary_key)
    for item in appdata.risks:
        i18n_keys.add(item.title_key)
    for rulepack in appdata.rulepacks.values():
        for rule in rulepack.rules:
            i18n_keys.add(rule.title_key)
            i18n_keys.add(rule.summary_key)
            effects = rule.effects if isinstance(rule.effects, dict) else {}
            for checklist in effects.get("add_checklist", []) or []:
                i18n_keys.add(checklist)
        for kit in rulepack.compliance_kits:
            i18n_keys.add(kit.title_key)
            i18n_keys.add(kit.summary_key)
            for checklist in kit.checklist:
                i18n_keys.add(checklist)
    missing_i18n = sorted(key for key in i18n_keys if key and key not in en_translations)
    if missing_i18n:
        fatals.append(("validate.missing_i18n_keys", {"keys": ", ".join(missing_i18n)}))

    if workspace is not None:
        paths = get_workspace_paths(workspace)
        reviews_path = paths.reviews / "reviews.yaml"
        if reviews_path.exists():
            review_errors = validate_reviews_data(load_yaml(reviews_path) or {})
            fatals.extend(review_errors)
        evidence_fatals, evidence_warns = validate_registry(workspace)
        fatals.extend(evidence_fatals)
        warns.extend(evidence_warns)
        if appdata.data_sources:
            overlay_count = len(
                [source for source in appdata.data_sources.values() if source == "overlay"]
            )
            canonical_count = len(
                [source for source in appdata.data_sources.values() if source == "canonical"]
            )
            warns.append(
                (
                    "validate.source_summary",
                    {"overlay": overlay_count, "canonical": canonical_count},
                )
            )

    return fatals, warns
