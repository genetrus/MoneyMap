"""Load data artifacts from disk."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from money_map.core.model import (
    AppData,
    DataSourceInfo,
    Meta,
    Rule,
    Rulepack,
    StalenessPolicy,
    Variant,
)
from money_map.storage.fs import read_mapping, read_yaml


def _resolve_data_file(*candidates: Path) -> Path:
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "No data file found. Tried: " + ", ".join(str(path) for path in candidates)
    )


def _iso_mtime(path: Path) -> str:
    return datetime.utcfromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat()


def _safe_read_mapping(path: Path) -> dict[str, Any]:
    try:
        return read_mapping(path)
    except Exception:
        return {}


def _items_count(payload: dict[str, Any], source_type: str) -> int:
    list_keys = {
        "variants": "variants",
        "rulepack": "rules",
        "bridges": "bridges",
        "routes": "routes",
        "occupation_map": "maps",
        "keywords": "keywords",
        "mappings": "taxonomy",
    }
    key = list_keys.get(source_type)
    if key:
        value = payload.get(key, [])
        if isinstance(value, dict):
            return len(value)
        if isinstance(value, list):
            return len(value)
    return len(payload) if isinstance(payload, dict) else 0


def _detect_source_type(path: Path) -> str:
    if path.name == "meta.yaml":
        return "meta"
    if path.parts[-2:] == ("rulepacks", "DE.yaml") or path.name == "rulepack.yaml":
        return "rulepack"
    if path.name.startswith("variants"):
        return "variants"
    if path.name.startswith("bridges"):
        return "bridges"
    if path.name.startswith("routes"):
        return "routes"
    if path.name == "occupation_map.yaml":
        return "occupation_map"
    if path.name == "keywords.yaml":
        return "keywords"
    if path.name == "mappings.yaml":
        return "mappings"
    if "overlay" in path.name:
        return "overlay"
    if "generated" in path.name:
        return "generated"
    return "data"


def _collect_source_registry(data_dir: Path) -> list[DataSourceInfo]:
    candidates: list[Path] = []
    core_known = [
        data_dir / "meta.yaml",
        data_dir / "rulepacks" / "DE.yaml",
        data_dir / "variants.yaml",
        data_dir / "keywords.yaml",
        data_dir / "mappings.yaml",
    ]
    candidates.extend([p for p in core_known if p.exists()])

    for subdir in ("packs", "overlays", "generated", "rulepacks"):
        base = data_dir / subdir
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.yaml")):
            candidates.append(path)
        for path in sorted(base.rglob("*.yml")):
            candidates.append(path)
        for path in sorted(base.rglob("*.json")):
            candidates.append(path)

    # Add meta-like and pack sidecars that may exist outside nested folders.
    for path in sorted(data_dir.glob("*.yaml")):
        if path not in candidates:
            candidates.append(path)
    for path in sorted(data_dir.glob("*.json")):
        if path not in candidates:
            candidates.append(path)

    unique = sorted({p.resolve() for p in candidates})
    registry: list[DataSourceInfo] = []
    for path in unique:
        if not path.is_file():
            continue
        payload = _safe_read_mapping(path)
        source_type = _detect_source_type(path)
        reviewed_at_raw = payload.get("reviewed_at") if isinstance(payload, dict) else ""
        schema_version_raw = payload.get("schema_version") if isinstance(payload, dict) else ""
        notes: dict[str, Any] = {
            "group": (
                "pack"
                if "/packs/" in path.as_posix()
                else "overlay"
                if "/overlays/" in path.as_posix()
                else "generated"
                if "/generated/" in path.as_posix()
                else "core"
            )
        }
        if path.name.startswith("variants") and not reviewed_at_raw and source_type == "variants":
            variants = payload.get("variants", []) if isinstance(payload, dict) else []
            review_dates = [str(v.get("review_date", "")) for v in variants if isinstance(v, dict)]
            review_dates = [d for d in review_dates if d]
            if review_dates:
                reviewed_at_raw = min(review_dates)
                notes["reviewed_at_derived_from"] = "variants[].review_date"

        try:
            source_path = path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            source_path = path.as_posix()

        registry.append(
            DataSourceInfo(
                source=source_path,
                type=source_type,
                schema_version=str(schema_version_raw or ""),
                items=_items_count(payload, source_type),
                reviewed_at=str(reviewed_at_raw or ""),
                mtime=_iso_mtime(path),
                notes=notes,
            )
        )

    return sorted(registry, key=lambda item: item.source)


def _load_meta(meta_path: Path) -> Meta:
    raw = read_mapping(meta_path)
    staleness_policy = raw.get("staleness_policy", {})
    return Meta(
        dataset_version=str(raw.get("dataset_version", "")),
        staleness_policy=StalenessPolicy(
            warn_after_days=int(
                staleness_policy.get(
                    "warn_after_days", staleness_policy.get("stale_after_days", 180)
                )
            ),
            hard_after_days=int(staleness_policy.get("hard_after_days", 365)),
        ),
    )


def _load_rulepack(rulepack_path: Path, meta_policy: StalenessPolicy) -> Rulepack:
    raw = read_mapping(rulepack_path)
    staleness_policy_raw = raw.get("staleness_policy") or {}
    staleness_policy = StalenessPolicy(
        warn_after_days=int(
            staleness_policy_raw.get(
                "warn_after_days",
                staleness_policy_raw.get("stale_after_days", meta_policy.warn_after_days),
            )
        ),
        hard_after_days=int(
            staleness_policy_raw.get("hard_after_days", meta_policy.hard_after_days)
        ),
    )
    rules = [Rule(rule_id=r["rule_id"], reason=r.get("reason", "")) for r in raw.get("rules", [])]
    return Rulepack(
        reviewed_at=str(raw.get("reviewed_at", "")),
        staleness_policy=staleness_policy,
        compliance_kits=raw.get("compliance_kits", {}),
        regulated_domains=raw.get("regulated_domains", []),
        rules=rules,
    )


def _load_variants(variants_path: Path) -> list[Variant]:
    raw = read_mapping(variants_path)
    variants: list[Variant] = []
    for entry in raw.get("variants", []):
        variants.append(
            Variant(
                variant_id=str(entry.get("variant_id", "")),
                title=str(entry.get("title", "")),
                summary=str(entry.get("summary", "")),
                cell_id=str(entry.get("cell_id", "")),
                taxonomy_id=str(entry.get("taxonomy_id", "")),
                tags=list(entry.get("tags", [])),
                regulated_domain=(
                    None
                    if entry.get("regulated_domain") in (None, "")
                    else str(entry.get("regulated_domain"))
                ),
                feasibility=entry.get("feasibility", {}),
                prep_steps=list(entry.get("prep_steps", [])),
                economics=entry.get("economics", {}),
                legal=entry.get("legal", {}),
                review_date=str(entry.get("review_date", "")),
            )
        )
    return variants


def load_app_data(data_dir: str | Path = "data") -> AppData:
    data_dir = Path(data_dir)
    meta_path = _resolve_data_file(data_dir / "meta.yaml", data_dir / "meta.json")
    variants_path = _resolve_data_file(data_dir / "variants.yaml", data_dir / "variants.json")
    rulepack_path = _resolve_data_file(
        data_dir / "rulepacks" / "DE.yaml",
        data_dir / "rulepacks" / "DE.json",
    )

    meta = _load_meta(meta_path)
    rulepack = _load_rulepack(rulepack_path, meta.staleness_policy)
    variants = _load_variants(variants_path)
    sources = _collect_source_registry(data_dir)
    return AppData(meta=meta, rulepack=rulepack, variants=variants, sources=sources)


def load_profile(profile_path: str | Path) -> dict[str, Any]:
    return read_yaml(profile_path)
