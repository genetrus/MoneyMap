from __future__ import annotations

import hashlib
import json
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


@dataclass(frozen=True)
class ConflictReport:
    entity_ref: str
    canonical_hash: str | None
    overlay_hash: str | None
    conflict_type: str
    suggested_action: str


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


def _load_yaml_file(path: Path) -> Any:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(content) or {}
    return {}


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _required_keys_for_entity(entity_type: str) -> list[str]:
    if entity_type == "variant":
        return [
            "variant_id",
            "title_key",
            "summary_key",
            "taxonomy_id",
            "cells",
            "tags",
            "review_date",
            "feasibility",
            "economics",
            "legal",
            "evidence",
            "required_skills",
            "required_assets",
            "constraints",
            "objectives",
            "risks",
        ]
    if entity_type == "taxonomy":
        return ["taxonomy_id", "title_key"]
    if entity_type == "cell":
        return ["cell_id", "title_key"]
    if entity_type == "preset":
        return [
            "preset_id",
            "title_key",
            "summary_key",
            "weight_feasibility",
            "weight_economics",
            "weight_legal",
            "weight_fit",
            "weight_staleness",
        ]
    if entity_type == "rulepack":
        return ["country_code", "reviewed_at", "rules", "compliance_kits"]
    return []


def _overlay_files_for_prefix(overlay_dir: Path, prefix: str) -> list[Path]:
    files = sorted(overlay_dir.glob(f"{prefix}*.yaml"))
    resolved = [path for path in files if ".resolved" in path.stem]
    regular = [path for path in files if ".resolved" not in path.stem]
    return regular + resolved


def _load_list_items(path: Path) -> list[dict[str, Any]]:
    data = _load_yaml_file(path)
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def detect_workspace_conflicts(data_dir: Path, workspace: Path) -> list[ConflictReport]:
    conflicts: list[ConflictReport] = []
    paths = get_workspace_paths(workspace)
    if not paths.overlay.exists():
        return conflicts

    entity_specs = {
        "taxonomy": ("taxonomy.yaml", "taxonomy_id"),
        "cell": ("cells.yaml", "cell_id"),
        "variant": ("variants.yaml", "variant_id"),
        "preset": ("presets.yaml", "preset_id"),
    }

    for entity_type, (filename, id_key) in entity_specs.items():
        canonical_path = data_dir / filename
        canonical_items = {item.get(id_key): item for item in _load_list_items(canonical_path)}
        overlay_files = _overlay_files_for_prefix(paths.overlay, filename.split(".")[0])
        overlay_items: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
        for path in overlay_files:
            for item in _load_list_items(path):
                item_id = str(item.get(id_key, ""))
                if not item_id:
                    continue
                overlay_items.setdefault(item_id, []).append((path, item))

        for item_id, entries in overlay_items.items():
            if len(entries) > 1:
                overlay_hashes = sorted(_hash_payload(entry[1]) for entry in entries)
                conflicts.append(
                    ConflictReport(
                        entity_ref=f"{entity_type}:{item_id}",
                        canonical_hash=_hash_payload(canonical_items[item_id])
                        if item_id in canonical_items
                        else None,
                        overlay_hash=_hash_payload({"items": overlay_hashes}),
                        conflict_type="overlay_collision",
                        suggested_action="resolve_precedence",
                    )
                )
            required_keys = _required_keys_for_entity(entity_type)
            for _, item in entries:
                if item_id in canonical_items and any(key not in item for key in required_keys):
                    conflicts.append(
                        ConflictReport(
                            entity_ref=f"{entity_type}:{item_id}",
                            canonical_hash=_hash_payload(canonical_items[item_id]),
                            overlay_hash=_hash_payload(item),
                            conflict_type="overlay_incomplete",
                            suggested_action="use_canonical_or_manual",
                        )
                    )

    canonical_rulepacks: dict[str, dict[str, Any]] = {}
    rulepacks_dir = data_dir / "rulepacks"
    if rulepacks_dir.exists():
        for path in sorted(rulepacks_dir.glob("*.yaml")):
            payload = _load_yaml_file(path)
            if isinstance(payload, dict):
                code = (payload.get("country_code") or path.stem).upper()
                canonical_rulepacks[code] = payload

    overlay_rulepacks: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    if paths.overlay_rulepacks.exists():
        for path in sorted(paths.overlay_rulepacks.glob("*.yaml")):
            payload = _load_yaml_file(path)
            if not isinstance(payload, dict):
                continue
            code = (payload.get("country_code") or path.stem).upper()
            overlay_rulepacks.setdefault(code, []).append((path, payload))

    for code, entries in overlay_rulepacks.items():
        if len(entries) > 1:
            overlay_hashes = sorted(_hash_payload(entry[1]) for entry in entries)
            conflicts.append(
                ConflictReport(
                    entity_ref=f"rulepack:{code}",
                    canonical_hash=_hash_payload(canonical_rulepacks[code])
                    if code in canonical_rulepacks
                    else None,
                    overlay_hash=_hash_payload({"items": overlay_hashes}),
                    conflict_type="overlay_collision",
                    suggested_action="resolve_precedence",
                )
            )
        required_keys = _required_keys_for_entity("rulepack")
        for _, payload in entries:
            if code in canonical_rulepacks and any(key not in payload for key in required_keys):
                conflicts.append(
                    ConflictReport(
                        entity_ref=f"rulepack:{code}",
                        canonical_hash=_hash_payload(canonical_rulepacks[code]),
                        overlay_hash=_hash_payload(payload),
                        conflict_type="overlay_incomplete",
                        suggested_action="use_canonical_or_manual",
                    )
                )

    return sorted(conflicts, key=lambda item: item.entity_ref)


def resolve_workspace_conflict(
    data_dir: Path, workspace: Path, entity_ref: str, resolution: str
) -> Path:
    paths = get_workspace_paths(workspace)
    if ":" not in entity_ref:
        raise ValueError("entity_ref must include ':'")
    entity_type, entity_id = entity_ref.split(":", 1)
    entity_id = entity_id.strip()
    if not entity_id:
        raise ValueError("entity_ref id missing")

    canonical_payload: dict[str, Any] | None = None
    overlay_payload: dict[str, Any] | None = None
    target_path: Path

    if entity_type == "rulepack":
        canonical_path = data_dir / "rulepacks" / f"{entity_id.upper()}.yaml"
        canonical_payload = (
            _load_yaml_file(canonical_path) if canonical_path.exists() else None
        )
        overlay_files = sorted(paths.overlay_rulepacks.glob("*.yaml"))
        overlay_entries = []
        for path in overlay_files:
            payload = _load_yaml_file(path)
            if isinstance(payload, dict) and (
                (payload.get("country_code") or path.stem).upper() == entity_id.upper()
            ):
                overlay_entries.append(payload)
        if overlay_entries:
            overlay_payload = overlay_entries[-1]
        target_path = paths.overlay_rulepacks / f"{entity_id.upper()}.resolved.yaml"
    else:
        entity_map = {
            "taxonomy": ("taxonomy.yaml", "taxonomy_id"),
            "cell": ("cells.yaml", "cell_id"),
            "variant": ("variants.yaml", "variant_id"),
            "preset": ("presets.yaml", "preset_id"),
        }
        if entity_type not in entity_map:
            raise ValueError("Unknown entity type")
        filename, id_key = entity_map[entity_type]
        canonical_items = _load_list_items(data_dir / filename)
        canonical_payload = next(
            (item for item in canonical_items if str(item.get(id_key, "")) == entity_id),
            None,
        )
        overlay_files = _overlay_files_for_prefix(paths.overlay, filename.split(".")[0])
        overlay_items: list[dict[str, Any]] = []
        for path in overlay_files:
            overlay_items.extend(
                [
                    item
                    for item in _load_list_items(path)
                    if str(item.get(id_key, "")) == entity_id
                ]
            )
        if overlay_items:
            overlay_payload = overlay_items[-1]
        target_path = paths.overlay / f"{filename.split('.')[0]}.resolved.yaml"

    if resolution not in {"canonical", "overlay", "manual"}:
        raise ValueError("Unknown resolution mode")
    if resolution == "canonical":
        payload = canonical_payload
    elif resolution == "overlay":
        payload = overlay_payload
    else:
        payload = merge_dict(canonical_payload or {}, overlay_payload or {})
    if payload is None:
        raise ValueError("Unable to resolve entity")

    if entity_type == "rulepack":
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(dump_yaml(payload), encoding="utf-8")
    else:
        current = _load_yaml_file(target_path)
        items = current if isinstance(current, list) else []
        id_key = _required_keys_for_entity(entity_type)[0]
        updated = False
        for index, item in enumerate(items):
            if isinstance(item, dict) and str(item.get(id_key, "")) == entity_id:
                items[index] = payload
                updated = True
                break
        if not updated:
            items.append(payload)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(dump_yaml(items), encoding="utf-8")

    config = _load_yaml_file(paths.config) or {}
    if not isinstance(config, dict):
        config = {}
    resolved = config.get("resolved_conflicts", [])
    if not isinstance(resolved, list):
        resolved = []
    resolved.append(
        {
            "entity_ref": entity_ref,
            "resolution": resolution,
            "resolved_at": date.today().isoformat(),
            "path": str(target_path.relative_to(paths.root)),
        }
    )
    config["resolved_conflicts"] = resolved
    paths.config.write_text(dump_yaml(config), encoding="utf-8")
    return target_path
