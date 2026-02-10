"""MoneyMap CLI."""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import typer

from money_map.app.api import (
    classify_idea,
    export_bundle,
    plan_variant,
    recommend_variants,
    validate_data,
)
from money_map.app.observability import get_run_context, init_run_context, log_exception
from money_map.core.errors import DataValidationError, InternalError, MoneyMapError
from money_map.storage.fs import write_json

app = typer.Typer(help="MoneyMap CLI.")

_NETWORK_GUARD_ENV = "MONEY_MAP_DISABLE_NETWORK"


def _disable_network() -> None:
    message = f"Network access disabled by {_NETWORK_GUARD_ENV}=1"

    def _blocked(*_args, **_kwargs):
        raise RuntimeError(message)

    socket.socket.connect = _blocked  # type: ignore[assignment]
    socket.socket.connect_ex = _blocked  # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]


def _disable_network_if_requested() -> None:
    flag = os.getenv(_NETWORK_GUARD_ENV, "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        _disable_network()


def _issue_codes(issues: list[dict]) -> list[str]:
    return [issue.get("code", "") for issue in issues if issue.get("code")]


def _format_report(report: dict) -> str:
    fatal_codes = _issue_codes(report["fatals"])
    warn_codes = _issue_codes(report["warns"])
    lines = [
        "validation report",
        f"status: {report['status']}",
        f"dataset_version: {report['dataset_version']}",
        f"reviewed_at: {report['reviewed_at']}",
        f"stale: {report['stale']}",
        f"staleness_policy_days: {report['staleness_policy_days']}",
        f"fatals: {len(report['fatals'])}",
        f"warns: {len(report['warns'])}",
    ]
    if report["fatals"]:
        lines.append("FATALS:")
        lines.extend([f"- {fatal}" for fatal in fatal_codes])
    if report["warns"]:
        lines.append("WARNS:")
        lines.extend([f"- {warn}" for warn in warn_codes])
    staleness = report.get("staleness", {})
    if staleness:
        lines.append("STALENESS:")
        rulepack = staleness.get("rulepack", {})
        if rulepack:
            lines.append(f"- rulepack: {rulepack.get('message')}")
        variant_map = staleness.get("variants", {})
        stale_variants = [
            variant_id for variant_id, detail in variant_map.items() if detail.get("is_stale")
        ]
        if stale_variants:
            lines.append(f"- stale_variants: {', '.join(sorted(stale_variants))}")
    return "\n".join(lines)


def _render_error(err: MoneyMapError) -> None:
    run_id = err.run_id or (get_run_context().run_id if get_run_context() else "unknown")
    typer.echo(f"[ERROR {err.code}] {err.message} (run_id={run_id})", err=True)
    if err.hint:
        typer.echo(f"Hint: {err.hint}", err=True)
    if err.details:
        typer.echo(f"Details: {err.details}", err=True)


def _streamlit_installed() -> bool:
    return importlib.util.find_spec("streamlit") is not None


def _ui_install_hints() -> list[str]:
    return [
        'python -m pip install -e ".[ui]"',
        "python scripts/install_ui_deps.py",
        "python scripts/install_ui_offline.py --wheelhouse wheelhouse",
    ]


def _print_ui_install_guidance() -> None:
    typer.echo("Streamlit is not installed in this Python environment.")
    typer.echo("Install UI dependencies with one of these commands:")
    for command in _ui_install_hints():
        typer.echo(f"  - {command}")


def _install_ui_dependencies() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "install_ui_deps.py"
    return subprocess.run([sys.executable, str(script_path)], cwd=repo_root, check=False).returncode


def _summarize_legal_reasons(checklist: list[str]) -> str | None:
    markers = ("DATE_INVALID", "DATA_STALE")
    highlighted: list[str] = []
    for marker in markers:
        highlighted.extend([item for item in checklist if marker in str(item)])
    if highlighted:
        return "; ".join(highlighted[:2])
    if checklist:
        return "see legal_checklist"
    return None


@app.command()
def validate(
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
) -> None:
    """Validate datasets and rules."""
    run_context = init_run_context("validate", data_dir)
    try:
        report = validate_data(data_dir)
        typer.echo(_format_report(report))
        if report["fatals"]:
            fatal_codes = _issue_codes(report["fatals"])
            error = DataValidationError(
                message=f"Validation failed with fatals: {', '.join(fatal_codes)}",
                hint="Fix the fatals and rerun `money-map validate`.",
                run_id=run_context.run_id,
                details=report.get("report_path"),
                extra={"fatals": report["fatals"]},
            )
            _render_error(error)
            raise typer.Exit(code=1)
    except MoneyMapError as exc:
        _render_error(exc)
        raise typer.Exit(code=1)
    except Exception as exc:
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Check logs for details.",
            run_id=run_context.run_id,
        )
        _render_error(error)
        log_exception("Unhandled validate exception", run_id=run_context.run_id)
        raise typer.Exit(code=1)


@app.command()
def recommend(
    profile: str = typer.Option(..., "--profile", help="Path to profile YAML"),
    top: int = typer.Option(5, "--top", help="Top N variants"),
    objective: str = typer.Option("fastest_money", "--objective", help="Objective preset"),
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json"),
    output_path: str | None = typer.Option(None, "--output", help="Write JSON output to file"),
) -> None:
    """Recommend top variants."""
    run_context = init_run_context("recommend", data_dir)
    try:
        result = recommend_variants(profile, objective=objective, top_n=top, data_dir=data_dir)
        output_format = output_format.strip().lower()
        if output_format not in {"text", "json"}:
            raise MoneyMapError(
                code="INVALID_FORMAT",
                message="Output format must be 'text' or 'json'.",
                hint="Use --format text or --format json.",
                run_id=run_context.run_id,
            )

        payload = {
            "run_id": run_context.run_id,
            "objective": objective,
            "top_n": top,
            "profile_hash": result.profile_hash,
            "recommendations": [
                {
                    "variant_id": rec.variant.variant_id,
                    "score": rec.score,
                    "title": rec.variant.title,
                    "pros": rec.pros,
                    "cons": rec.cons,
                    "explanations": {
                        "pros": rec.pros,
                        "cons": rec.cons,
                        "legal_checklist": rec.legal.checklist,
                    },
                    "stale": rec.stale,
                    "staleness": rec.staleness,
                    "legal_gate": rec.legal.legal_gate,
                    "legal_checklist": rec.legal.checklist,
                    "applied_rules": [asdict(rule) for rule in rec.legal.applied_rules],
                }
                for rec in result.ranked_variants
            ],
            "diagnostics": result.diagnostics,
        }

        if output_path:
            write_json(output_path, payload, default=str)

        if output_format == "json":
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
            return

        for idx, rec in enumerate(result.ranked_variants, start=1):
            typer.echo(
                f"{idx}. {rec.variant.variant_id} | score={rec.score:.2f} | {rec.variant.title}"
            )
            typer.echo(f"   Pros: {'; '.join(rec.pros)}")
            if rec.cons:
                typer.echo(f"   Cons: {'; '.join(rec.cons)}")
            if rec.stale:
                typer.echo("   Warning: data is stale")
            if rec.legal.legal_gate != "ok":
                typer.echo(f"   Legal gate: {rec.legal.legal_gate}")
                reason = _summarize_legal_reasons(rec.legal.checklist)
                if reason:
                    typer.echo(f"   Reason: {reason}")
        typer.echo(
            json.dumps(
                {"diagnostics": result.diagnostics, "run_id": run_context.run_id},
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
    except MoneyMapError as exc:
        _render_error(exc)
        raise typer.Exit(code=1)
    except Exception as exc:
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Check logs for details.",
            run_id=run_context.run_id,
        )
        _render_error(error)
        log_exception("Unhandled recommend exception", run_id=run_context.run_id)
        raise typer.Exit(code=1)




@app.command()
def classify(
    idea_text: str = typer.Option(..., "--idea-text", help="Free-text idea to classify"),
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
    output_format: str = typer.Option("text", "--format", help="Output format: text or json"),
) -> None:
    """Classify idea text into taxonomy + cell with deterministic explanations."""
    run_context = init_run_context("classify", data_dir)
    try:
        result = classify_idea(idea_text=idea_text, data_dir=data_dir)
        output_format = output_format.strip().lower()
        if output_format not in {"text", "json"}:
            raise MoneyMapError(
                code="INVALID_FORMAT",
                message="Output format must be 'text' or 'json'.",
                hint="Use --format text or --format json.",
                run_id=run_context.run_id,
            )

        payload = {
            "run_id": run_context.run_id,
            "idea_text": result.idea_text,
            "cell_guess": result.cell_guess,
            "backup_cell_guess": result.backup_cell_guess,
            "matched_keywords": result.matched_keywords,
            "suggested_tags": result.suggested_tags,
            "reasons": result.reasons,
            "confidence": result.confidence,
            "ambiguity": result.ambiguity,
            "top3": [
                {
                    "taxonomy_id": candidate.taxonomy_id,
                    "taxonomy_label": candidate.taxonomy_label,
                    "score": candidate.score,
                    "cell_guess": candidate.cell_guess,
                    "reasons": candidate.reasons,
                }
                for candidate in result.top3
            ],
        }

        if output_format == "json":
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        typer.echo(f"cell_guess: {result.cell_guess}")
        typer.echo(f"ambiguity: {result.ambiguity} | confidence={result.confidence:.2f}")
        if result.matched_keywords:
            typer.echo(f"matched_keywords: {', '.join(result.matched_keywords)}")
        for idx, candidate in enumerate(result.top3, start=1):
            typer.echo(
                f"{idx}. {candidate.taxonomy_id} | score={candidate.score:.2f} "
                f"| cell={candidate.cell_guess}"
            )
            if candidate.reasons:
                typer.echo(f"   reasons: {'; '.join(candidate.reasons[:3])}")
    except MoneyMapError as exc:
        _render_error(exc)
        raise typer.Exit(code=1)
    except Exception as exc:
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Check logs for details.",
            run_id=run_context.run_id,
        )
        _render_error(error)
        log_exception("Unhandled classify exception", run_id=run_context.run_id)
        raise typer.Exit(code=1)


@app.command()
def plan(
    profile: str = typer.Option(..., "--profile", help="Path to profile YAML"),
    variant_id: str = typer.Option(..., "--variant-id", help="Variant ID"),
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
) -> None:
    """Generate a route plan for a selected variant."""
    run_context = init_run_context("plan", data_dir)
    try:
        plan_data = plan_variant(profile, variant_id, data_dir=data_dir)
        typer.echo(f"Plan for {plan_data.variant_id} with {len(plan_data.steps)} steps ready.")
    except MoneyMapError as exc:
        _render_error(exc)
        raise typer.Exit(code=1)
    except Exception as exc:
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Check logs for details.",
            run_id=run_context.run_id,
        )
        _render_error(error)
        log_exception("Unhandled plan exception", run_id=run_context.run_id)
        raise typer.Exit(code=1)


@app.command()
def export(
    profile: str = typer.Option(..., "--profile", help="Path to profile YAML"),
    variant_id: str = typer.Option(..., "--variant-id", help="Variant ID"),
    out_dir: str = typer.Option("exports", "--out", help="Output directory"),
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
) -> None:
    """Export plan artifacts."""
    run_context = init_run_context("export", data_dir, out_dir=out_dir)
    try:
        paths = export_bundle(profile, variant_id, out_dir=out_dir, data_dir=data_dir)
        typer.echo("Exported:")
        typer.echo(f"- {paths['plan']}")
        typer.echo(f"- {paths['result']}")
        typer.echo(f"- {paths['profile']}")
    except MoneyMapError as exc:
        _render_error(exc)
        raise typer.Exit(code=1)
    except Exception as exc:
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Check logs for details.",
            run_id=run_context.run_id,
        )
        _render_error(error)
        log_exception("Unhandled export exception", run_id=run_context.run_id)
        raise typer.Exit(code=1)


@app.command()
def ui(
    install: bool = typer.Option(
        False,
        "--install",
        help="Attempt to install UI dependencies before launching Streamlit.",
    ),
) -> None:
    """Launch the UI."""
    if not _streamlit_installed():
        if install:
            typer.echo("Installing UI dependencies...")
            status = _install_ui_dependencies()
            if status != 0:
                _print_ui_install_guidance()
                raise typer.Exit(code=status)
        if not _streamlit_installed():
            _print_ui_install_guidance()
            raise typer.Exit(code=1)

    app_path = Path(__file__).resolve().parents[1] / "ui" / "app.py"
    process = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=False,
    )
    if process.returncode != 0:
        raise typer.Exit(code=process.returncode)


def main() -> None:
    _disable_network_if_requested()
    try:
        app()
    except MoneyMapError as exc:
        _render_error(exc)
        raise typer.Exit(code=1)
    except Exception as exc:
        run_id = get_run_context().run_id if get_run_context() else str(uuid4())
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Check logs for details.",
            run_id=run_id,
        )
        _render_error(error)
        log_exception("Unhandled CLI exception", run_id=run_id)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
