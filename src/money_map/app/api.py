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

_VALIDATION_FATALS_MESSAGE = "Validation failed with fatals"


class ValidationFatalsError(ValueError):
    def __init__(self, fatals: list[str]) -> None:
        self.fatals = fatals
        super().__init__(f"{_VALIDATION_FATALS_MESSAGE}: {', '.join(fatals)}")


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
        "staleness": report.staleness,
    }


def _raise_on_fatals(report) -> None:
    if report.fatals:
        raise ValidationFatalsError(report.fatals)


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
    report = validate(app_data)
    _raise_on_fatals(report)
    profile = _resolve_profile(profile_path, profile_data)
    return recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        objective,
        filters,
        top_n,
    )


def plan_variant(
    profile_path: str | Path | None,
    variant_id: str,
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
):
    app_data = load_app_data(data_dir)
    report = validate(app_data)
    _raise_on_fatals(report)
    profile = _resolve_profile(profile_path, profile_data)
    variant = next((v for v in app_data.variants if v.variant_id == variant_id), None)
    if variant is None:
        raise ValueError(f"Variant '{variant_id}' not found.")
    plan = build_plan(profile, variant, app_data.rulepack, app_data.meta.staleness_policy)
    return plan


def export_bundle(
    profile_path: str | Path | None,
    variant_id: str,
    out_dir: str | Path = "exports",
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
) -> dict[str, str]:
    app_data = load_app_data(data_dir)
    report = validate(app_data)
    _raise_on_fatals(report)
    profile = _resolve_profile(profile_path, profile_data)
    variant = next((v for v in app_data.variants if v.variant_id == variant_id), None)
    if variant is None:
        raise ValueError(f"Variant '{variant_id}' not found.")
    recommendations = recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        "fastest_money",
        {},
        len(app_data.variants),
    )
    selected = next(
        (r for r in recommendations.ranked_variants if r.variant.variant_id == variant_id), None
    )
    if selected is None:
        raise ValueError(f"Variant '{variant_id}' not found in recommendations.")
    plan = build_plan(profile, variant, app_data.rulepack, app_data.meta.staleness_policy)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "plan.md"
    result_path = out_dir / "result.json"
    profile_path_out = out_dir / "profile.yaml"
    artifacts_dir = out_dir / "artifacts"

    write_text(plan_path, render_plan_md(plan))
    write_json(result_path, render_result_json(profile, selected, plan))
    write_yaml(profile_path_out, profile)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    checklist_lines = ["# Compliance Checklist", "", f"Legal gate: {plan.legal_gate}", ""]
    checklist_lines.extend([f"- {item}" for item in plan.compliance])
    budget_payload = {
        "currency": "EUR",
        "budget_items": [
            {"item": "Initial tools", "estimated_cost_eur": 0},
            {"item": "Marketing", "estimated_cost_eur": 0},
        ],
        "notes": "Fill in actual costs based on your plan.",
    }
    outreach_lines = [
        "Subject: Quick intro",
        "",
        f"Hi there, I am starting {selected.variant.title}.",
        f"{selected.variant.summary}",
        "",
        "Would you be open to a short chat to validate the offer?",
        "",
        "Thanks,",
        profile.get("name", "Your name"),
    ]

    artifact_paths = []
    for artifact in plan.artifacts:
        artifact_path = out_dir / artifact
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        if artifact_path.name == "checklist.md":
            write_text(artifact_path, "\n".join(checklist_lines) + "\n")
        elif artifact_path.name == "budget.yaml":
            write_yaml(artifact_path, budget_payload)
        elif artifact_path.name == "outreach_message.txt":
            write_text(artifact_path, "\n".join(outreach_lines) + "\n")
        elif not artifact_path.exists():
            if artifact_path.suffix in {".yaml", ".yml"}:
                write_yaml(artifact_path, {"placeholder": True})
            elif artifact_path.suffix == ".md":
                write_text(artifact_path, "# Placeholder\n")
            elif artifact_path.suffix == ".txt":
                write_text(artifact_path, "Placeholder\n")
            else:
                write_text(artifact_path, "")
        artifact_paths.append(str(artifact_path))

    return {
        "plan": str(plan_path),
        "result": str(result_path),
        "profile": str(profile_path_out),
        "artifacts": artifact_paths,
    }
