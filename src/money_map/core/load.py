from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from money_map.core.model import AppData, Cell, Meta, RulePack, TaxonomyItem, Variant


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_app_data(data_dir: Path, country_code: str = "DE") -> AppData:
    meta = Meta.model_validate(load_yaml(data_dir / "meta.yaml"))
    raw_taxonomy = load_yaml(data_dir / "taxonomy.yaml")
    raw_cells = load_yaml(data_dir / "cells.yaml")
    raw_variants = load_yaml(data_dir / "variants.yaml")
    taxonomy_items = [
        TaxonomyItem.model_validate(item) for item in raw_taxonomy if isinstance(raw_taxonomy, list)
    ]
    cells = [Cell.model_validate(item) for item in raw_cells if isinstance(raw_cells, list)]
    variants = [
        Variant.model_validate(item) for item in raw_variants if isinstance(raw_variants, list)
    ]
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
