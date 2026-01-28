from __future__ import annotations

from functools import lru_cache
from importlib import resources
from typing import Any

import yaml

SUPPORTED_LANGS = ["en", "de", "fr", "es", "pl", "ru"]


@lru_cache(maxsize=None)
def _load_lang(lang: str) -> dict[str, Any]:
    if lang not in SUPPORTED_LANGS:
        lang = "en"
    with (
        resources.files("money_map.i18n")
        .joinpath(f"{lang}.yaml")
        .open("r", encoding="utf-8") as handle
    ):
        return yaml.safe_load(handle) or {}


def t(key: str, lang: str, **kwargs: Any) -> str:
    selected = _load_lang(lang)
    en = _load_lang("en")
    value = selected.get(key) or en.get(key) or key
    if not isinstance(value, str):
        value = str(value)
    try:
        return value.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return value
