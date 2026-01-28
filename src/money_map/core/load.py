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
    Cell,
    Meta,
    RulePack,
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
    variants = [Variant.model_validate(item) for item in _ensure_list(raw_variants)]
    bridges = load_yaml(data_dir / "bridges.yaml") or []
    rulepack_path = data_dir / "rulepacks" / f"{country_code}.yaml"
    rulepack = RulePack.model_validate(load_yaml(rulepack_path))
    return AppData(
        meta=meta,
        taxonomy=taxonomy_items,
        cells=cells,
        variants=variants,
        bridges=bridges,
        rulepack=rulepack,
    )
