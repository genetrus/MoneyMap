from __future__ import annotations

from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

ID_KEYS = [
    "preset_id",
    "taxonomy_id",
    "cell_id",
    "variant_id",
    "skill_id",
    "asset_id",
    "constraint_id",
    "objective_id",
    "risk_id",
    "rule_id",
    "kit_id",
    "country_code",
]


def _sort_list(items: list[Any]) -> list[Any]:
    if not items:
        return items
    if all(isinstance(item, dict) for item in items):
        for key in ID_KEYS:
            if all(key in item for item in items):
                return sorted(items, key=lambda item: str(item.get(key, "")))
    return items


def normalize_data(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: normalize_data(data[key]) for key in sorted(data.keys())}
    if isinstance(data, list):
        normalized = [normalize_data(item) for item in data]
        return _sort_list(normalized)
    return data


def dump_yaml(data: Any) -> str:
    normalized = normalize_data(data)
    if yaml:
        return yaml.safe_dump(
            normalized,
            sort_keys=True,
            allow_unicode=True,
            default_flow_style=False,
        )
    lines: list[str] = []
    if isinstance(normalized, dict):
        for key, value in normalized.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines).rstrip() + "\n"
    return str(normalized)
