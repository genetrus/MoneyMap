from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from money_map.core.evidence import validate_registry
from money_map.core.load import load_app_data, load_yaml
from money_map.core.reviews import validate_reviews_data
from money_map.core.workspace import detect_workspace_conflicts, get_workspace_paths
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
    "rulepacks/PL.yaml",
    "rulepacks/FR.yaml",
    "rulepacks/ES.yaml",
    "knowledge/skills.yaml",
    "knowledge/assets.yaml",
    "knowledge/constraints.yaml",
    "knowledge/objectives.yaml",
    "knowledge/risks.yaml",
]
OPTIONAL_FILES: list[str] = []
VALIDATION_CACHE_FILE = ".money_map_validation_cache.json"


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


def _fingerprint_file(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def _collect_validation_files(
    data_dir: Path, workspace: Path | None
) -> dict[str, tuple[int, int]]:
    paths: set[Path] = set()
    for rel in REQUIRED_FILES + OPTIONAL_FILES:
        path = data_dir / rel
        if path.exists():
            paths.add(path)
    rulepacks_dir = data_dir / "rulepacks"
    if rulepacks_dir.exists():
        paths.update(rulepacks_dir.glob("*.yaml"))
    if workspace is not None:
        paths_obj = get_workspace_paths(workspace)
        if paths_obj.overlay.exists():
            paths.update(paths_obj.overlay.glob("*.yaml"))
            if paths_obj.overlay_rulepacks.exists():
                paths.update(paths_obj.overlay_rulepacks.glob("*.yaml"))
        reviews_path = paths_obj.reviews / "reviews.yaml"
        if reviews_path.exists():
            paths.add(reviews_path)
        registry_path = paths_obj.evidence / "registry.yaml"
        if registry_path.exists():
            paths.add(registry_path)
    return {str(path.resolve()): _fingerprint_file(path) for path in paths}


def _cache_path(data_dir: Path) -> Path:
    return data_dir / VALIDATION_CACHE_FILE


def _load_validation_cache(data_dir: Path) -> dict[str, object] | None:
    path = _cache_path(data_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _save_validation_cache(
    data_dir: Path,
    workspace: Path | None,
    fingerprints: dict[str, tuple[int, int]],
    sections: dict[str, dict[str, list[tuple[str, dict]]]],
) -> None:
    payload = {
        "data_dir": str(data_dir.resolve()),
        "workspace": str(workspace.resolve()) if workspace else None,
        "run_date": date.today().isoformat(),
        "fingerprints": {key: list(value) for key, value in fingerprints.items()},
        "sections": sections,
    }
    _cache_path(data_dir).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sections_for_path(path: Path, data_dir: Path, workspace: Path | None) -> set[str]:
    rel = None
    if path.is_relative_to(data_dir):
        rel = path.relative_to(data_dir).as_posix()
    elif workspace is not None and path.is_relative_to(workspace):
        rel = path.relative_to(workspace).as_posix()
    if rel is None:
        return set()
    if rel == "meta.yaml":
        return {"meta", "staleness", "i18n", "rulepacks"}
    if rel in {"taxonomy.yaml", "cells.yaml", "variants.yaml"}:
        return {"variants", "bridges", "i18n"}
    if rel == "bridges.yaml":
        return {"bridges"}
    if rel == "presets.yaml":
        return {"lookups", "i18n"}
    if rel.startswith("knowledge/"):
        return {"lookups", "variants", "i18n"}
    if rel.startswith("rulepacks/"):
        return {"rulepacks", "staleness", "i18n"}
    if rel.startswith("overlay/"):
        if rel.startswith("overlay/rulepacks/"):
            return {"rulepacks", "staleness", "i18n"}
        if rel.startswith("overlay/bridges"):
            return {"bridges"}
        if rel.startswith("overlay/variants") or rel.startswith("overlay/taxonomy") or rel.startswith(
            "overlay/cells"
        ):
            return {"variants", "bridges", "i18n"}
        if rel.startswith("overlay/presets") or rel.startswith("overlay/knowledge"):
            return {"lookups", "i18n"}
        return {"variants", "rulepacks", "lookups", "i18n"}
    if rel == "reviews/reviews.yaml":
        return {"workspace"}
    if rel == "evidence/registry.yaml":
        return {"workspace"}
    return set()


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


def _validate_meta_section(appdata) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals: list[tuple[str, dict]] = []
    warns: list[tuple[str, dict]] = []
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
    return fatals, warns


def _validate_variants_section(appdata) -> list[tuple[str, dict]]:
    fatals: list[tuple[str, dict]] = []
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
    return fatals


def _validate_bridges_section(data_dir: Path, variant_ids: list[str]) -> list[tuple[str, dict]]:
    fatals: list[tuple[str, dict]] = []
    bridges = load_yaml(data_dir / "bridges.yaml")
    if isinstance(bridges, list):
        for bridge in bridges:
            if not isinstance(bridge, dict):
                fatals.append(("validate.bridge_invalid", {}))
                continue
            missing = [key for key in ("from_variant_id", "to_variant_id") if key not in bridge]
            if missing:
                fatals.append(("validate.bridge_missing_keys", {"keys": ", ".join(missing)}))
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
    return fatals


def _validate_lookup_sections(data_dir: Path) -> list[tuple[str, dict]]:
    fatals: list[tuple[str, dict]] = []
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
    return fatals


def _validate_rulepack_section(appdata) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals: list[tuple[str, dict]] = []
    warns: list[tuple[str, dict]] = []
    for country_code, rulepack in appdata.rulepacks.items():
        fatals.extend(
            _ensure_keys(
                f"rulepack:{country_code}",
                rulepack.model_dump()
                if hasattr(rulepack, "model_dump")
                else rulepack.__dict__,
                [
                    "country_code",
                    "reviewed_at",
                    "rules",
                    "compliance_kits",
                ],
            )
        )
        if rulepack.is_placeholder and not rulepack.placeholder_notice_key:
            fatals.append(
                ("validate.rulepack_placeholder_notice", {"country_code": country_code})
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
            fatals.append(("validate.rulepack_country_mismatch", {"country_code": country_code}))

    rulepack_reviewed = _to_date(appdata.rulepack.reviewed_at)
    days_since_rulepack = (date.today() - rulepack_reviewed).days
    if days_since_rulepack > appdata.meta.staleness_policy.warn_after_days:
        warns.append(("validate.rulepack_stale", {"days": days_since_rulepack}))

    if appdata.meta.supported_countries:
        missing_rulepacks = [
            code for code in appdata.meta.supported_countries if code not in appdata.rulepacks
        ]
        if missing_rulepacks:
            fatals.append(
                ("validate.missing_rulepack", {"country_codes": ", ".join(missing_rulepacks)})
            )
    return fatals, warns


def _validate_staleness_section(appdata) -> list[tuple[str, dict]]:
    warns: list[tuple[str, dict]] = []
    today = date.today()
    meta_reviewed = _to_date(appdata.meta.reviewed_at)
    rulepack_reviewed = _to_date(appdata.rulepack.reviewed_at)
    policy = appdata.meta.staleness_policy
    require_check_stale = (
        (today - meta_reviewed).days > policy.force_require_check_after_days
        or (today - rulepack_reviewed).days > policy.force_require_check_after_days
    )
    if require_check_stale:
        regulated_tags = set(policy.regulated_tags)
        for variant in appdata.variants:
            if regulated_tags.intersection(variant.tags):
                warns.append(
                    (
                        "validate.regulated_requires_check",
                        {"variant_id": variant.variant_id},
                    )
                )
    return warns


def _validate_i18n_section(appdata) -> list[tuple[str, dict]]:
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
        if rulepack.placeholder_notice_key:
            i18n_keys.add(rulepack.placeholder_notice_key)
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
        return [("validate.missing_i18n_keys", {"keys": ", ".join(missing_i18n)})]
    return []


def _validate_workspace_section(
    appdata, data_dir: Path, workspace: Path | None, strict: bool
) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    if workspace is None:
        return [], []
    fatals: list[tuple[str, dict]] = []
    warns: list[tuple[str, dict]] = []
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
    conflicts = detect_workspace_conflicts(data_dir, workspace)
    if conflicts:
        regulated_variants = {
            variant.variant_id
            for variant in appdata.variants
            if variant.legal.regulated_level != "none" or "regulated" in variant.tags
        }
        regulated_conflicts = [
            item
            for item in conflicts
            if item.entity_ref.startswith("variant:")
            and item.entity_ref.split(":", 1)[1] in regulated_variants
        ]
        if regulated_conflicts:
            target = fatals if strict else warns
            for item in regulated_conflicts:
                target.append(
                    (
                        "validate.workspace_conflict",
                        {"entity_ref": item.entity_ref},
                    )
                )
    return fatals, warns


def validate_app_data(
    data_dir: Path,
    strict: bool = False,
    workspace: Path | None = None,
    incremental: bool = False,
) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    fatals, warns = validate_files_exist(data_dir, strict)
    if fatals:
        return fatals, warns

    fingerprints = _collect_validation_files(data_dir, workspace)
    cache = _load_validation_cache(data_dir) if incremental else None
    sections_to_run: set[str] = {
        "meta",
        "variants",
        "bridges",
        "lookups",
        "rulepacks",
        "staleness",
        "i18n",
        "workspace",
    }
    cached_sections: dict[str, dict[str, list[tuple[str, dict]]]] = {}
    if incremental and cache:
        cache_date = cache.get("run_date")
        cache_workspace = cache.get("workspace")
        cache_data_dir = cache.get("data_dir")
        cache_fingerprints = cache.get("fingerprints", {})
        if (
            cache_date == date.today().isoformat()
            and cache_workspace == (str(workspace.resolve()) if workspace else None)
            and cache_data_dir == str(data_dir.resolve())
        ):
            changed = []
            for key, value in fingerprints.items():
                cached = cache_fingerprints.get(key)
                if cached != list(value):
                    changed.append(Path(key))
            if len(changed) == 1 and isinstance(cache.get("sections"), dict):
                sections_to_run = _sections_for_path(changed[0], data_dir, workspace)
                cached_sections = cache.get("sections", {})  # type: ignore[assignment]
                for section, payload in list(cached_sections.items()):
                    if not isinstance(payload, dict):
                        cached_sections.pop(section, None)
                        continue
                    for key in ("fatals", "warns"):
                        entries = payload.get(key, [])
                        if isinstance(entries, list):
                            payload[key] = [
                                tuple(item) if isinstance(item, list) else item for item in entries
                            ]
                if not sections_to_run:
                    sections_to_run = {
                        "meta",
                        "variants",
                        "bridges",
                        "lookups",
                        "rulepacks",
                        "staleness",
                        "i18n",
                        "workspace",
                    }
                    cached_sections = {}
    appdata = load_app_data(data_dir, workspace=workspace)
    section_results: dict[str, dict[str, list[tuple[str, dict]]]] = {
        key: {"fatals": [], "warns": []} for key in sections_to_run
    }

    if "meta" in sections_to_run:
        meta_fatals, meta_warns = _validate_meta_section(appdata)
        section_results["meta"]["fatals"].extend(meta_fatals)
        section_results["meta"]["warns"].extend(meta_warns)
    if "variants" in sections_to_run:
        variant_fatals = _validate_variants_section(appdata)
        section_results["variants"]["fatals"].extend(variant_fatals)
    if "bridges" in sections_to_run:
        bridge_fatals = _validate_bridges_section(
            data_dir, [variant.variant_id for variant in appdata.variants]
        )
        section_results["bridges"]["fatals"].extend(bridge_fatals)
    if "lookups" in sections_to_run:
        lookup_fatals = _validate_lookup_sections(data_dir)
        section_results["lookups"]["fatals"].extend(lookup_fatals)
    if "rulepacks" in sections_to_run:
        rulepack_fatals, rulepack_warns = _validate_rulepack_section(appdata)
        section_results["rulepacks"]["fatals"].extend(rulepack_fatals)
        section_results["rulepacks"]["warns"].extend(rulepack_warns)
    if "staleness" in sections_to_run:
        staleness_warns = _validate_staleness_section(appdata)
        section_results["staleness"]["warns"].extend(staleness_warns)
    if "i18n" in sections_to_run:
        i18n_fatals = _validate_i18n_section(appdata)
        section_results["i18n"]["fatals"].extend(i18n_fatals)
    if "workspace" in sections_to_run:
        workspace_fatals, workspace_warns = _validate_workspace_section(
            appdata, data_dir, workspace, strict
        )
        section_results["workspace"]["fatals"].extend(workspace_fatals)
        section_results["workspace"]["warns"].extend(workspace_warns)

    merged_sections = dict(cached_sections)
    merged_sections.update(section_results)

    for section in merged_sections.values():
        fatals.extend(section.get("fatals", []))
        warns.extend(section.get("warns", []))

    if incremental:
        _save_validation_cache(data_dir, workspace, fingerprints, merged_sections)
    return fatals, warns
