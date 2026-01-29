from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from money_map.core.model import (
    AppData,
    Asset,
    Cell,
    ComplianceKit,
    Constraint,
    EconomicsSnapshot,
    Evidence,
    Feasibility,
    Legal,
    Meta,
    Objective,
    Risk,
    Rule,
    RulePack,
    Skill,
    StalenessPolicy,
    TaxonomyItem,
    Variant,
)


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.lower() in {"null", "none"}:
        return None
    if value.startswith("[") or value.startswith("{"):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
    if value.startswith('"') and value.endswith('"'):
        return value.strip('"')
    if value.startswith("'") and value.endswith("'"):
        return value.strip("'")
    try:
        return int(value)
    except ValueError:
        return value


def _parse_block(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start
    if lines[start].lstrip().startswith("- "):
        items: list[Any] = []
        index = start
        while index < len(lines):
            line = lines[index]
            current_indent = len(line) - len(line.lstrip())
            if current_indent < indent or not line.strip():
                break
            if not line.lstrip().startswith("- ") or current_indent != indent:
                break
            content = line.lstrip()[2:].strip()
            index += 1
            if content:
                if ":" in content:
                    key, value = content.split(":", 1)
                    item: dict[str, Any] = {key.strip(): _parse_scalar(value)}
                    if index < len(lines):
                        next_indent = len(lines[index]) - len(lines[index].lstrip())
                        if next_indent > indent:
                            nested, index = _parse_block(lines, index, next_indent)
                            if isinstance(nested, dict):
                                item.update(nested)
                    items.append(item)
                else:
                    items.append(_parse_scalar(content))
            else:
                nested, index = _parse_block(lines, index, indent + 2)
                items.append(nested)
        return items, index

    mapping: dict[str, Any] = {}
    index = start
    while index < len(lines):
        line = lines[index]
        current_indent = len(line) - len(line.lstrip())
        if current_indent < indent or not line.strip():
            break
        if current_indent != indent:
            index += 1
            continue
        key, value = line.lstrip().split(":", 1)
        key = key.strip()
        value = value.strip()
        index += 1
        if value:
            mapping[key] = _parse_scalar(value)
        else:
            nested, index = _parse_block(lines, index, indent + 2)
            mapping[key] = nested
    return mapping, index


def _safe_load_basic(text: str) -> Any:
    stripped = text.strip()
    if stripped in {"", "null", "None"}:
        return None
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            return ast.literal_eval(stripped)
        except (SyntaxError, ValueError):
            return stripped
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    parsed, _ = _parse_block(lines, 0, len(lines[0]) - len(lines[0].lstrip()))
    return parsed


def load_mapping(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        content = handle.read()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        if yaml:
            return yaml.safe_load(content) or {}
        raise ValueError(
            "PyYAML not installed; either install pyyaml or make data files JSON-compatible YAML."
        ) from None


def load_yaml(path: Path) -> Any:
    return load_mapping(path)


def _ensure_list(data: Any) -> list[Any]:
    return data if isinstance(data, list) else []


def _sort_by_id(items: list[Any], id_key: str) -> list[Any]:
    return sorted(
        items,
        key=lambda item: getattr(item, id_key, "")
        if hasattr(item, id_key)
        else str(item.get(id_key, "")),
    )


def _sort_bridges(bridges: list[Any]) -> list[Any]:
    def _bridge_key(item: Any) -> tuple[str, str]:
        if hasattr(item, "get"):
            return (str(item.get("from_variant_id", "")), str(item.get("to_variant_id", "")))
        return ("", "")

    return sorted(bridges, key=_bridge_key)


def load_app_data(data_dir: Path, country_code: str = "DE") -> AppData:
    meta_data = load_yaml(data_dir / "meta.yaml")
    staleness = meta_data.get("staleness_policy") if isinstance(meta_data, dict) else None
    if isinstance(staleness, dict):
        meta_data["staleness_policy"] = StalenessPolicy.model_validate(staleness)
    meta = Meta.model_validate(meta_data)
    raw_taxonomy = load_yaml(data_dir / "taxonomy.yaml")
    raw_cells = load_yaml(data_dir / "cells.yaml")
    raw_variants = load_yaml(data_dir / "variants.yaml")
    taxonomy_items = [TaxonomyItem.model_validate(item) for item in _ensure_list(raw_taxonomy)]
    cells = [Cell.model_validate(item) for item in _ensure_list(raw_cells)]
    def _normalize_variant(variant: Variant) -> Variant:
        if isinstance(variant.feasibility, dict):
            variant.feasibility = Feasibility.model_validate(variant.feasibility)
        if isinstance(variant.economics, dict):
            variant.economics = EconomicsSnapshot.model_validate(variant.economics)
        if isinstance(variant.legal, dict):
            variant.legal = Legal.model_validate(variant.legal)
        if isinstance(variant.evidence, dict):
            variant.evidence = Evidence.model_validate(variant.evidence)
        return variant

    variants = [
        _normalize_variant(Variant.model_validate(item))
        for item in _ensure_list(raw_variants)
    ]
    skills_path = data_dir / "knowledge" / "skills.yaml"
    assets_path = data_dir / "knowledge" / "assets.yaml"
    constraints_path = data_dir / "knowledge" / "constraints.yaml"
    objectives_path = data_dir / "knowledge" / "objectives.yaml"
    risks_path = data_dir / "knowledge" / "risks.yaml"

    skills = [Skill.model_validate(item) for item in _ensure_list(load_yaml(skills_path))]
    assets = [Asset.model_validate(item) for item in _ensure_list(load_yaml(assets_path))]
    constraints = [
        Constraint.model_validate(item)
        for item in _ensure_list(load_yaml(constraints_path))
    ]
    objectives = [
        Objective.model_validate(item)
        for item in _ensure_list(load_yaml(objectives_path))
    ]
    risks = [Risk.model_validate(item) for item in _ensure_list(load_yaml(risks_path))]
    bridges = load_yaml(data_dir / "bridges.yaml") or []
    if isinstance(bridges, list):
        bridges = _sort_bridges(bridges)
    rulepacks_dir = data_dir / "rulepacks"
    rulepacks: dict[str, RulePack] = {}
    if rulepacks_dir.exists():
        for path in sorted(rulepacks_dir.glob("*.yaml")):
            raw_pack = load_yaml(path) or {}
            raw_rules = [Rule.model_validate(item) for item in _ensure_list(raw_pack.get("rules"))]
            raw_kits = [
                ComplianceKit.model_validate(item)
                for item in _ensure_list(raw_pack.get("compliance_kits"))
            ]
            raw_pack["rules"] = _sort_by_id(raw_rules, "rule_id")
            raw_pack["compliance_kits"] = _sort_by_id(raw_kits, "kit_id")
            rulepack = RulePack.model_validate(raw_pack)
            rulepacks[rulepack.country_code] = rulepack
    if country_code not in rulepacks:
        rulepacks[country_code] = RulePack.model_validate(
            load_yaml(rulepacks_dir / f"{country_code}.yaml")
        )
    rulepack = rulepacks[country_code]
    return AppData(
        meta=meta,
        taxonomy=_sort_by_id(taxonomy_items, "taxonomy_id"),
        cells=_sort_by_id(cells, "cell_id"),
        variants=_sort_by_id(variants, "variant_id"),
        bridges=bridges,
        skills=_sort_by_id(skills, "skill_id"),
        assets=_sort_by_id(assets, "asset_id"),
        constraints=_sort_by_id(constraints, "constraint_id"),
        objectives=_sort_by_id(objectives, "objective_id"),
        risks=_sort_by_id(risks, "risk_id"),
        rulepacks=rulepacks,
        rulepack=rulepack,
    )
