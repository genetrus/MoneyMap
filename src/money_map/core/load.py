"""Load data artifacts from disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from money_map.core.model import AppData, Meta, Rule, Rulepack, StalenessPolicy, Variant
from money_map.storage.fs import read_yaml


def _load_meta(meta_path: Path) -> Meta:
    raw = read_yaml(meta_path)
    staleness_policy = raw.get("staleness_policy", {})
    return Meta(
        dataset_version=str(raw.get("dataset_version", "")),
        staleness_policy=StalenessPolicy(
            stale_after_days=int(staleness_policy.get("stale_after_days", 180))
        ),
    )


def _load_rulepack(rulepack_path: Path, meta_policy: StalenessPolicy) -> Rulepack:
    raw = read_yaml(rulepack_path)
    staleness_policy_raw = raw.get("staleness_policy") or {}
    staleness_policy = StalenessPolicy(
        stale_after_days=int(staleness_policy_raw.get("stale_after_days", meta_policy.stale_after_days))
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
    raw = read_yaml(variants_path)
    variants: list[Variant] = []
    for entry in raw.get("variants", []):
        variants.append(
            Variant(
                variant_id=str(entry.get("variant_id", "")),
                title=str(entry.get("title", "")),
                summary=str(entry.get("summary", "")),
                tags=list(entry.get("tags", [])),
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
    meta = _load_meta(data_dir / "meta.yaml")
    rulepack = _load_rulepack(data_dir / "rulepacks" / "DE.yaml", meta.staleness_policy)
    variants = _load_variants(data_dir / "variants.yaml")
    return AppData(meta=meta, rulepack=rulepack, variants=variants)


def load_profile(profile_path: str | Path) -> dict[str, Any]:
    return read_yaml(profile_path)
