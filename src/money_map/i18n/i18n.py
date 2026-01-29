from __future__ import annotations

from functools import lru_cache
from importlib import resources
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

SUPPORTED_LANGS = ["en", "de", "fr", "es", "pl", "ru"]


def _parse_flat_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        data[key] = value
    return data


@lru_cache(maxsize=None)
def load_lang(lang: str) -> dict[str, Any]:
    if lang not in SUPPORTED_LANGS:
        lang = "en"
    with (
        resources.files("money_map.i18n")
        .joinpath(f"{lang}.yaml")
        .open("r", encoding="utf-8") as handle
    ):
        content = handle.read()
    if yaml:
        return yaml.safe_load(content) or {}
    return _parse_flat_yaml(content)


def t(key: str, lang: str, **kwargs: Any) -> str:
    selected = load_lang(lang)
    en = load_lang("en")
    value = selected.get(key) or en.get(key) or key
    if not isinstance(value, str):
        value = str(value)
    try:
        return value.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return value
