"""Thin API wrapper for core functionality."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from money_map.app.observability import get_run_context, log_event
from money_map.core.errors import DataValidationError, MoneyMapError
from money_map.core.graph import build_plan
from money_map.core.load import load_app_data, load_profile
from money_map.core.profile import profile_hash
from money_map.core.recommend import recommend
from money_map.core.validate import validate
from money_map.render.plan_md import render_plan_md
from money_map.render.result_json import render_result_json
from money_map.storage.fs import write_json, write_text, write_yaml


def _validation_payload(report) -> dict[str, Any]:
    return {
        "status": report.status,
        "fatals": report.fatals,
        "warns": report.warns,
        "dataset_version": report.dataset_version,
        "reviewed_at": report.reviewed_at,
        "stale": report.stale,
        "staleness_policy_days": report.staleness_policy_days,
        "generated_at": report.generated_at,
        "staleness": report.staleness,
    }


def _issue_codes(issues: list[dict[str, Any]]) -> list[str]:
    return [issue.get("code", "") for issue in issues]


def _write_validation_report(
    payload: dict[str, Any],
    out_dir: str | Path | None,
    run_id: str | None,
) -> str | None:
    if not out_dir or not run_id:
        return None
    report_path = Path(out_dir) / f"validate-report-{run_id}.json"
    write_json(report_path, payload, default=str)
    return str(report_path)


def _validate_app_data(app_data, out_dir: str | Path | None, run_id: str | None):
    start = perf_counter()
    report = validate(app_data)
    duration_ms = (perf_counter() - start) * 1000
    payload = _validation_payload(report)
    payload["timings_ms"] = {"validate": round(duration_ms, 2)}
    report_path = _write_validation_report(payload, out_dir, run_id)
    payload["report_path"] = report_path
    return report, payload


def _raise_on_fatals(report, payload: dict[str, Any], run_id: str | None) -> None:
    if report.fatals:
        fatal_codes = _issue_codes(report.fatals)
        hint = "Fix the fatals and rerun `money-map validate` before continuing."
        details = payload.get("report_path") or "See validate report output."
        raise DataValidationError(
            message=f"Validation failed with fatals: {', '.join(fatal_codes)}",
            hint=hint,
            run_id=run_id,
            details=details,
            extra={"fatals": report.fatals},
        )


def validate_data(data_dir: str | Path = "data") -> dict[str, Any]:
    app_data = load_app_data(data_dir)
    run_context = get_run_context()
    report, payload = _validate_app_data(
        app_data,
        run_context.out_dir if run_context else None,
        run_context.run_id if run_context else None,
    )
    log_event(
        "validate",
        run_id=run_context.run_id if run_context else None,
        dataset_version=payload["dataset_version"],
        reviewed_at=payload["reviewed_at"],
        stale=payload["stale"],
        fatals=len(payload["fatals"]),
        warns=len(payload["warns"]),
        report_path=payload.get("report_path"),
        timings_ms=payload.get("timings_ms"),
    )
    return payload


def _resolve_profile(profile_path: str | Path | None, profile_data: dict | None) -> dict:
    if profile_data is not None:
        return profile_data
    if profile_path is None:
        raise MoneyMapError(
            code="PROFILE_MISSING",
            message="Profile path is required when no profile data is provided.",
            hint="Provide --profile or pass profile_data in API calls.",
        )
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
    run_context = get_run_context()
    report, payload = _validate_app_data(
        app_data,
        run_context.out_dir if run_context else None,
        run_context.run_id if run_context else None,
    )
    _raise_on_fatals(report, payload, run_context.run_id if run_context else None)
    profile = _resolve_profile(profile_path, profile_data)
    start = perf_counter()
    result = recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        objective,
        filters,
        top_n,
    )
    duration_ms = (perf_counter() - start) * 1000
    diagnostics = dict(result.diagnostics)
    diagnostics.setdefault("warnings", {})
    if report.stale:
        diagnostics["warnings"].setdefault("stale_rulepack", 0)
        diagnostics["warnings"]["stale_rulepack"] += 1
    diagnostics["timings_ms"] = {
        "validate": payload["timings_ms"]["validate"],
        "recommend": round(duration_ms, 2),
    }
    log_event(
        "recommend",
        run_id=run_context.run_id if run_context else None,
        dataset_version=payload["dataset_version"],
        reviewed_at=payload["reviewed_at"],
        stale=payload["stale"],
        profile_hash=result.profile_hash,
        objective=objective,
        top_n=top_n,
        timings_ms=diagnostics.get("timings_ms"),
        filtered_out=diagnostics.get("filtered_out"),
    )
    return result.__class__(
        ranked_variants=result.ranked_variants,
        diagnostics=diagnostics,
        profile_hash=result.profile_hash,
    )


def plan_variant(
    profile_path: str | Path | None,
    variant_id: str,
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
):
    app_data = load_app_data(data_dir)
    run_context = get_run_context()
    report, payload = _validate_app_data(
        app_data,
        run_context.out_dir if run_context else None,
        run_context.run_id if run_context else None,
    )
    _raise_on_fatals(report, payload, run_context.run_id if run_context else None)
    profile = _resolve_profile(profile_path, profile_data)
    variant = next((v for v in app_data.variants if v.variant_id == variant_id), None)
    if variant is None:
        raise MoneyMapError(
            code="VARIANT_NOT_FOUND",
            message=f"Variant '{variant_id}' not found.",
            hint="Pick a variant_id from `money-map recommend` output.",
            run_id=run_context.run_id if run_context else None,
        )
    plan = build_plan(profile, variant, app_data.rulepack, app_data.meta.staleness_policy)
    log_event(
        "plan",
        run_id=run_context.run_id if run_context else None,
        dataset_version=payload["dataset_version"],
        reviewed_at=payload["reviewed_at"],
        stale=payload["stale"],
        variant_id=variant_id,
        profile_hash=profile_hash(profile),
    )
    return plan


def export_bundle(
    profile_path: str | Path | None,
    variant_id: str,
    out_dir: str | Path = "exports",
    data_dir: str | Path = "data",
    profile_data: dict | None = None,
) -> dict[str, str]:
    app_data = load_app_data(data_dir)
    run_context = get_run_context()
    report, payload = _validate_app_data(
        app_data,
        run_context.out_dir if run_context else None,
        run_context.run_id if run_context else None,
    )
    _raise_on_fatals(report, payload, run_context.run_id if run_context else None)
    profile = _resolve_profile(profile_path, profile_data)
    variant = next((v for v in app_data.variants if v.variant_id == variant_id), None)
    if variant is None:
        raise MoneyMapError(
            code="VARIANT_NOT_FOUND",
            message=f"Variant '{variant_id}' not found.",
            hint="Pick a variant_id from `money-map recommend` output.",
            run_id=run_context.run_id if run_context else None,
        )
    rec_start = perf_counter()
    recommendations = recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        "fastest_money",
        {},
        len(app_data.variants),
    )
    rec_duration_ms = (perf_counter() - rec_start) * 1000
    diagnostics = dict(recommendations.diagnostics)
    diagnostics.setdefault("warnings", {})
    if report.stale:
        diagnostics["warnings"].setdefault("stale_rulepack", 0)
        diagnostics["warnings"]["stale_rulepack"] += 1
    diagnostics["timings_ms"] = {
        "validate": payload["timings_ms"]["validate"],
        "recommend": round(rec_duration_ms, 2),
    }
    selected = next(
        (r for r in recommendations.ranked_variants if r.variant.variant_id == variant_id), None
    )
    if selected is None:
        raise MoneyMapError(
            code="VARIANT_NOT_FOUND",
            message=f"Variant '{variant_id}' not found in recommendations.",
            hint="Pick a variant_id from `money-map recommend` output.",
            run_id=run_context.run_id if run_context else None,
        )
    plan = build_plan(profile, variant, app_data.rulepack, app_data.meta.staleness_policy)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "plan.md"
    result_path = out_dir / "result.json"
    profile_path_out = out_dir / "profile.yaml"
    artifacts_dir = out_dir / "artifacts"

    write_text(plan_path, render_plan_md(plan))
    write_json(
        result_path,
        render_result_json(
            profile,
            selected,
            plan,
            diagnostics=diagnostics,
            profile_hash=recommendations.profile_hash,
            run_id=run_context.run_id if run_context else None,
        ),
    )
    write_yaml(profile_path_out, profile)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    log_event(
        "export",
        run_id=run_context.run_id if run_context else None,
        dataset_version=payload["dataset_version"],
        reviewed_at=payload["reviewed_at"],
        stale=payload["stale"],
        variant_id=variant_id,
        profile_hash=recommendations.profile_hash,
        result_path=str(result_path),
        timings_ms=diagnostics.get("timings_ms"),
    )

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
