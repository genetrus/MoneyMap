"""File system read/write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import yaml


def read_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file using safe loading."""
    payload = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(payload)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def write_yaml(path: str | Path, obj: Any) -> None:
    """Write YAML to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    path.write_text(payload, encoding="utf-8")


def write_json(
    path: str | Path,
    obj: Any,
    default: Callable[[Any], Any] | None = None,
) -> None:
    """Write JSON to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, ensure_ascii=False, indent=2, default=default)
    path.write_text(payload + "\n", encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    """Write plain text to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
