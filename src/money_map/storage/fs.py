"""File system read/write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import yaml


def _ensure_mapping(data: Any, path: str | Path, kind: str) -> dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{kind} root must be a mapping: {path}")
    return data


def read_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file using safe loading."""
    payload = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(payload)
    return _ensure_mapping(data, path, "YAML")


def read_json(path: str | Path) -> dict[str, Any]:
    """Read a JSON file."""
    payload = Path(path).read_text(encoding="utf-8")
    data = json.loads(payload)
    return _ensure_mapping(data, path, "JSON")


def read_mapping(path: str | Path) -> dict[str, Any]:
    """Read YAML/JSON mapping based on file extension."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        return read_json(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return read_yaml(path)
    raise ValueError(f"Unsupported mapping file extension: {path}")


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
