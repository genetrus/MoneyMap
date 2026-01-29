from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None
from money_map.core.yaml_utils import dump_yaml

WORKSPACE_VERSION = "0.5"


@dataclass
class WorkspacePaths:
    root: Path
    config: Path
    overlay: Path
    profiles: Path
    reviews: Path
    evidence: Path
    exports: Path
    evidence_files: Path
    overlay_rulepacks: Path


@dataclass
class WorkspaceStatus:
    overlay_files: list[str] = field(default_factory=list)
    review_count: int = 0
    last_reviewed_at: str | None = None
    evidence_count: int = 0
    evidence_file_count: int = 0


def get_workspace_paths(root: Path) -> WorkspacePaths:
    root = root.resolve()
    overlay = root / "overlay"
    evidence = root / "evidence"
    return WorkspacePaths(
        root=root,
        config=root / "config.yaml",
        overlay=overlay,
        profiles=root / "profiles",
        reviews=root / "reviews",
        evidence=evidence,
        exports=root / "exports",
        evidence_files=evidence / "files",
        overlay_rulepacks=overlay / "rulepacks",
    )


def ensure_within_workspace(root: Path, target: Path) -> Path:
    root = root.resolve()
    target = target.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path escapes workspace root") from exc
    return target


def init_workspace(root: Path) -> WorkspacePaths:
    paths = get_workspace_paths(root)
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.overlay.mkdir(parents=True, exist_ok=True)
    paths.overlay_rulepacks.mkdir(parents=True, exist_ok=True)
    (paths.overlay / "meta.yaml").touch(exist_ok=True)
    (paths.overlay / "taxonomy.yaml").touch(exist_ok=True)
    (paths.overlay / "cells.yaml").touch(exist_ok=True)
    (paths.overlay / "variants.yaml").touch(exist_ok=True)
    (paths.overlay / "bridges.yaml").touch(exist_ok=True)
    (paths.overlay / "presets.yaml").touch(exist_ok=True)
    paths.profiles.mkdir(parents=True, exist_ok=True)
    paths.reviews.mkdir(parents=True, exist_ok=True)
    paths.evidence_files.mkdir(parents=True, exist_ok=True)
    paths.exports.mkdir(parents=True, exist_ok=True)
    (paths.exports / ".gitkeep").touch(exist_ok=True)

    if not paths.config.exists():
        config_payload = {
            "workspace_version": WORKSPACE_VERSION,
            "created_at": date.today().isoformat(),
        }
        paths.config.write_text(dump_yaml(config_payload), encoding="utf-8")

    registry_path = paths.evidence / "registry.yaml"
    if not registry_path.exists():
        registry_path.write_text(dump_yaml({"items": []}), encoding="utf-8")

    reviews_path = paths.reviews / "reviews.yaml"
    if not reviews_path.exists():
        reviews_path.write_text(
            dump_yaml({"reviewed_at": date.today().isoformat(), "entries": []}),
            encoding="utf-8",
        )
    return paths


def workspace_status(root: Path) -> WorkspaceStatus:
    paths = get_workspace_paths(root)
    status = WorkspaceStatus()
    if paths.overlay.exists():
        status.overlay_files = sorted(
            str(path.relative_to(paths.root))
            for path in paths.overlay.glob("**/*.yaml")
            if path.is_file() and path.stat().st_size > 0
        )
    reviews_path = paths.reviews / "reviews.yaml"
    if reviews_path.exists():
        data = yaml.safe_load(reviews_path.read_text(encoding="utf-8")) if yaml else {}
        data = data or {}
        status.review_count = len(data.get("entries", []) or [])
        status.last_reviewed_at = data.get("reviewed_at")
    registry_path = paths.evidence / "registry.yaml"
    if registry_path.exists():
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) if yaml else {}
        data = data or {}
        items = data.get("items", []) or []
        status.evidence_count = len(items)
    if paths.evidence_files.exists():
        status.evidence_file_count = len(
            [item for item in paths.evidence_files.iterdir() if item.is_file()]
        )
    return status


def merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dict(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def merge_by_id(
    base: list[dict[str, Any]],
    overlay: list[dict[str, Any]],
    id_key: str,
    sources: dict[str, str],
    prefix: str,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in base:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get(id_key, ""))
        merged[item_id] = item
        sources[f"{prefix}:{item_id}"] = "canonical"
    for item in overlay:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get(id_key, ""))
        merged[item_id] = item
        sources[f"{prefix}:{item_id}"] = "overlay"
    return [merged[key] for key in sorted(merged.keys()) if key]


def merge_bridges(
    base: list[dict[str, Any]],
    overlay: list[dict[str, Any]],
    sources: dict[str, str],
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for item in base:
        if not isinstance(item, dict):
            continue
        key = (str(item.get("from_variant_id", "")), str(item.get("to_variant_id", "")))
        merged[key] = item
        sources[f"bridge:{key[0]}:{key[1]}"] = "canonical"
    for item in overlay:
        if not isinstance(item, dict):
            continue
        key = (str(item.get("from_variant_id", "")), str(item.get("to_variant_id", "")))
        merged[key] = item
        sources[f"bridge:{key[0]}:{key[1]}"] = "overlay"
    return [
        merged[key]
        for key in sorted(merged.keys(), key=lambda item: (item[0], item[1]))
        if key != ("", "")
    ]


def merge_rulepack(
    base: dict[str, Any],
    overlay: dict[str, Any],
    sources: dict[str, str],
    country_code: str,
) -> dict[str, Any]:
    merged = merge_dict(base, {k: v for k, v in overlay.items() if k not in {"rules", "compliance_kits"}})
    base_rules = base.get("rules", []) or []
    overlay_rules = overlay.get("rules", []) or []
    merged_rules = merge_by_id(
        base_rules,
        overlay_rules,
        "rule_id",
        sources,
        f"rulepack:{country_code}:rule",
    )
    base_kits = base.get("compliance_kits", []) or []
    overlay_kits = overlay.get("compliance_kits", []) or []
    merged_kits = merge_by_id(
        base_kits,
        overlay_kits,
        "kit_id",
        sources,
        f"rulepack:{country_code}:kit",
    )
    merged["rules"] = merged_rules
    merged["compliance_kits"] = merged_kits
    return merged
