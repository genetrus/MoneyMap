"""Thin API wrapper for core functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from money_map.core.graph import build_plan
from money_map.core.load import load_app_data, load_profile
from money_map.core.recommend import recommend
from money_map.core.validate import validate
from money_map.render.plan_md import render_plan_md
from money_map.render.result_json import render_result_json
from money_map.storage.fs import write_json, write_text, write_yaml


def validate_data(data_dir: str | Path = "data") -> dict[str, Any]:
    app_data = load_app_data(data_dir)
    report = validate(app_data)
    return {
        "status": report.status,
        "fatals": report.fatals,
        "warns": report.warns,
        "dataset_version": report.dataset_version,
        "reviewed_at": report.reviewed_at,
        "stale": report.stale,
    }


def _resolve_profile(profile_path: str | Path | None, profile_data: dict | None) -> dict:
    if profile_data is not None:
        return profile_data
    if profile_path is None:
        raise ValueError("profile_path is required when profile_data is not provided")
    return load_profile(profile_path)


def recommend_variants(
    profile_path: str | Path | None,
    objective: str = "fastest_money",
    filters: dict | None = None,
    top_n: int = 5,
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
):
    app_data = load_app_data(data_dir)
    profile = _resolve_profile(profile_path, profile_data)
    return recommend(profile, app_data.variants, app_data.rulepack, objective, filters, top_n)


def plan_variant(
    profile_path: str | Path | None,
    variant_id: str,
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
):
    app_data = load_app_data(data_dir)
    profile = _resolve_profile(profile_path, profile_data)
    variant = next(v for v in app_data.variants if v.variant_id == variant_id)
    plan = build_plan(profile, variant, app_data.rulepack)
    return plan


def export_bundle(
    profile_path: str | Path | None,
    variant_id: str,
    out_dir: str | Path = "exports",
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
) -> dict[str, str]:
    app_data = load_app_data(data_dir)
    profile = _resolve_profile(profile_path, profile_data)
    recommendations = recommend(profile, app_data.variants, app_data.rulepack, "fastest_money", {}, 10)
    selected = next(r for r in recommendations.ranked_variants if r.variant.variant_id == variant_id)
    plan = build_plan(profile, selected.variant, app_data.rulepack)

    out_dir = Path(out_dir)
    plan_path = out_dir / "plan.md"
    result_path = out_dir / "result.json"
    profile_path_out = out_dir / "profile.yaml"

    write_text(plan_path, render_plan_md(plan))
    write_json(result_path, render_result_json(profile, selected, plan))
    write_yaml(profile_path_out, profile)

    return {
        "plan": str(plan_path),
        "result": str(result_path),
        "profile": str(profile_path_out),
    }
