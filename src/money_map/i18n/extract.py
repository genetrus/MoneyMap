from __future__ import annotations

from pathlib import Path
from typing import Any

from money_map.core.load import load_yaml
from money_map.core.yaml_utils import dump_yaml
from money_map.i18n.audit import CORE_KEYS, _collect_dataset_keys
from money_map.i18n.i18n import load_lang

SPLIT_FILES = [
    "core.yaml",
    "ui.yaml",
    "cli.yaml",
    "reasons.yaml",
    "planner.yaml",
    "variants.yaml",
    "presets.yaml",
]


def _insert_nested(target: dict[str, Any], key: str) -> None:
    parts = key.split(".")
    current = target
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current.setdefault(parts[-1], "")


def extract_i18n_template(data_dir: Path, out: Path) -> None:
    dataset_keys = _collect_dataset_keys(data_dir)
    translations = load_lang("en")
    extra_keys = sorted(
        key
        for key in translations.keys()
        if key.startswith("reason.")
        or key.startswith("assumption.")
        or key.startswith("plan.")
        or key.startswith("sim.")
    )
    keys = sorted(set(CORE_KEYS).union(dataset_keys).union(extra_keys))
    template: dict[str, Any] = {}
    for key in keys:
        _insert_nested(template, key)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dump_yaml(template), encoding="utf-8")


def _split_key(key: str) -> str:
    if key.startswith("ui."):
        return "ui.yaml"
    if key.startswith("cli."):
        return "cli.yaml"
    if key.startswith("reason.") or key.startswith("assumption."):
        return "reasons.yaml"
    if key.startswith("plan."):
        return "planner.yaml"
    if key.startswith("variant."):
        return "variants.yaml"
    if key.startswith("preset."):
        return "presets.yaml"
    return "core.yaml"


def _flatten(prefix: str, node: Any, output: dict[str, str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            _flatten(new_prefix, value, output)
        return
    output[prefix] = "" if node is None else str(node)


def merge_translations(source: Path, lang: str, write: bool = False) -> dict[str, dict[str, str]]:
    data = load_yaml(source) or {}
    flat: dict[str, str] = {}
    _flatten("", data, flat)
    merged: dict[str, dict[str, str]] = {name: {} for name in SPLIT_FILES}
    for key, value in flat.items():
        target = _split_key(key)
        merged[target][key] = value

    if not write:
        return merged

    lang_dir = Path(__file__).resolve().parent / lang
    lang_dir.mkdir(parents=True, exist_ok=True)
    for filename, payload in merged.items():
        if not payload:
            continue
        out_path = lang_dir / filename
        out_path.write_text(dump_yaml(payload), encoding="utf-8")
    return merged
