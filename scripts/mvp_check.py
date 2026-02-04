#!/usr/bin/env python
"""Run MVP verification checks for MoneyMap."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from money_map.app.api import export_bundle, plan_variant, recommend_variants, validate_data
from money_map.core.model import Rule, Rulepack, StalenessPolicy, Variant
from money_map.core.rules import evaluate_legal
from money_map.render.plan_md import render_plan_md


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _record(results: list[CheckResult], name: str, status: str, detail: str) -> None:
    results.append(CheckResult(name=name, status=status, detail=detail))


def _print_results(results: list[CheckResult]) -> None:
    status_label, exit_code, failures, skips = _summarize_results(results)
    print("MVP CHECK RESULTS")
    for result in results:
        safe_name = result.name.replace("→", "->")
        print(f"{result.status}: {safe_name} - {result.detail}")
    print("-")
    print(f"Summary: {len(results)} checks, {failures} failed, {skips} skipped")
    print(status_label)


def _summarize_results(results: list[CheckResult]) -> tuple[str, int, int, int]:
    failures = sum(1 for result in results if result.status == "FAIL")
    skips = sum(1 for result in results if result.status == "SKIP")
    if failures:
        return "MVP FAILED", 1, failures, skips
    if skips:
        return "MVP INCOMPLETE", 2, failures, skips
    return "MVP PASSED", 0, failures, skips


def _check_validation(data_dir: Path) -> tuple[bool, str]:
    report = validate_data(data_dir)
    if report["status"] != "valid" or report["fatals"]:
        return False, f"status={report['status']} fatals={report['fatals']}"
    return True, f"dataset_version={report['dataset_version']}"


def _check_recommend_plan_export(
    data_dir: Path, profile: Path, top_n: int
) -> tuple[bool, str, str]:
    rec = recommend_variants(
        profile_path=profile, objective="fastest_money", top_n=top_n, data_dir=data_dir
    )
    if not rec.ranked_variants:
        return False, "no recommendations returned", ""
    variant_id = rec.ranked_variants[0].variant.variant_id
    plan = plan_variant(profile_path=profile, variant_id=variant_id, data_dir=data_dir)
    plan_md = render_plan_md(plan)
    if "## Compliance" not in plan_md:
        return False, "plan missing compliance section", variant_id
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = export_bundle(
            profile_path=profile, variant_id=variant_id, out_dir=tmpdir, data_dir=data_dir
        )
        expected = ["plan", "result", "profile"]
        missing = [key for key in expected if not Path(paths[key]).exists()]
        if missing:
            return False, f"missing exports: {missing}", variant_id
        artifact_missing = [p for p in paths.get("artifacts", []) if not Path(p).exists()]
        if artifact_missing:
            return False, f"missing artifacts: {artifact_missing}", variant_id
    return True, f"variant_id={variant_id}", variant_id


def _check_plan_actionability(data_dir: Path, profile: Path, variant_id: str) -> tuple[bool, str]:
    plan = plan_variant(profile_path=profile, variant_id=variant_id, data_dir=data_dir)
    if len(plan.steps) < 10:
        return False, f"steps={len(plan.steps)}"
    if len(plan.artifacts) < 3:
        return False, f"artifacts={len(plan.artifacts)}"
    return True, f"steps={len(plan.steps)} artifacts={len(plan.artifacts)}"


def _check_determinism(data_dir: Path, profile: Path, top_n: int) -> tuple[bool, str]:
    result_a = recommend_variants(
        profile_path=profile, objective="fastest_money", top_n=top_n, data_dir=data_dir
    )
    result_b = recommend_variants(
        profile_path=profile, objective="fastest_money", top_n=top_n, data_dir=data_dir
    )
    ids_a = [rec.variant.variant_id for rec in result_a.ranked_variants]
    ids_b = [rec.variant.variant_id for rec in result_b.ranked_variants]
    if ids_a != ids_b:
        return False, f"order mismatch: {ids_a} vs {ids_b}"
    return True, f"top_n={top_n}"


def _check_staleness_gating() -> tuple[bool, str]:
    policy = StalenessPolicy(stale_after_days=1)
    rulepack = Rulepack(
        reviewed_at="2000-01-01",
        staleness_policy=policy,
        compliance_kits={},
        regulated_domains=["regulated"],
        rules=[Rule(rule_id="de.legal.regulated.require_check_if_stale", reason="stale guard")],
    )
    variant = Variant(
        variant_id="regulated.stale",
        title="Regulated stale",
        summary="Summary",
        tags=["regulated"],
        feasibility={},
        prep_steps=[],
        economics={},
        legal={"legal_gate": "ok", "checklist": []},
        review_date="2000-01-01",
    )
    stale_result = evaluate_legal(rulepack, variant, policy)
    if stale_result.legal_gate != "require_check" or not any(
        "DATA_STALE" in item for item in stale_result.checklist
    ):
        return False, "stale regulated gating missing DATA_STALE"

    invalid_variant = Variant(
        variant_id="regulated.invalid",
        title="Regulated invalid",
        summary="Summary",
        tags=["regulated"],
        feasibility={},
        prep_steps=[],
        economics={},
        legal={"legal_gate": "ok", "checklist": []},
        review_date="not-a-date",
    )
    invalid_result = evaluate_legal(rulepack, invalid_variant, policy)
    if invalid_result.legal_gate != "require_check" or not any(
        "DATE_INVALID" in item for item in invalid_result.checklist
    ):
        return False, "unknown freshness gating missing DATE_INVALID"

    return True, "regulated gating markers present"


def _check_ui_import(mode: str) -> tuple[str, str]:
    if importlib.util.find_spec("streamlit") is None:
        detail = 'Streamlit missing. Run: python -m pip install -e ".[ui]"'
        if mode == "optional":
            return "SKIP", detail
        return "SKIP", f"(required) {detail}"
    from money_map.ui import app as ui_app

    if not hasattr(ui_app, "run_app"):
        return "FAIL", "UI module missing run_app"
    return "PASS", "streamlit UI import ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MoneyMap MVP checks")
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    parser.add_argument(
        "--profile",
        default="profiles/demo_fast_start.yaml",
        help="Path to profile YAML",
    )
    parser.add_argument("--top", type=int, default=5, help="Top-N for recommendations")
    args = parser.parse_args()

    data_dir = ROOT / args.data_dir
    profile = ROOT / args.profile
    ui_mode = (os.getenv("MM_UI_CHECK") or "required").strip().lower()
    if ui_mode not in {"required", "optional"}:
        ui_mode = "required"

    results: list[CheckResult] = []

    try:
        ok, detail = _check_validation(data_dir)
        _record(results, "Dataset validation", "PASS" if ok else "FAIL", detail)
    except Exception as exc:  # noqa: BLE001
        _record(results, "Dataset validation", "FAIL", str(exc))

    variant_id = ""
    try:
        ok, detail, variant_id = _check_recommend_plan_export(data_dir, profile, args.top)
        _record(results, "Recommend -> Plan -> Export", "PASS" if ok else "FAIL", detail)
    except Exception as exc:  # noqa: BLE001
        _record(results, "Recommend -> Plan -> Export", "FAIL", str(exc))

    try:
        if variant_id:
            ok, detail = _check_plan_actionability(data_dir, profile, variant_id)
            _record(results, "Plan actionability", "PASS" if ok else "FAIL", detail)
        else:
            _record(results, "Plan actionability", "FAIL", "missing variant_id")
    except Exception as exc:  # noqa: BLE001
        _record(results, "Plan actionability", "FAIL", str(exc))

    try:
        ok, detail = _check_determinism(data_dir, profile, args.top)
        _record(results, "Determinism", "PASS" if ok else "FAIL", detail)
    except Exception as exc:  # noqa: BLE001
        _record(results, "Determinism", "FAIL", str(exc))

    try:
        ok, detail = _check_staleness_gating()
        _record(results, "Staleness + regulated gating", "PASS" if ok else "FAIL", detail)
    except Exception as exc:  # noqa: BLE001
        _record(results, "Staleness + regulated gating", "FAIL", str(exc))

    try:
        status, detail = _check_ui_import(ui_mode)
        _record(results, "UI import smoke", status, detail)
    except Exception as exc:  # noqa: BLE001
        _record(results, "UI import smoke", "FAIL", str(exc))

    _print_results(results)

    _, exit_code, _, _ = _summarize_results(results)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
