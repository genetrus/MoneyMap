"""Centralized UI copy loader (RU-first, i18n-ready)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_COPY_DIR = Path("data/ui_copy")


@lru_cache(maxsize=4)
def load_copy(locale: str = "ru") -> dict[str, Any]:
    path = _COPY_DIR / f"{locale}.yaml"
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def copy_text(key: str, default: str = "", *, locale: str = "ru", **fmt: Any) -> str:
    node: Any = load_copy(locale)
    for part in key.split("."):
        if not isinstance(node, dict):
            node = None
            break
        node = node.get(part)

    if isinstance(node, str):
        value = node
    else:
        value = default

    if fmt:
        try:
            return value.format(**fmt)
        except Exception:
            return value
    return value
