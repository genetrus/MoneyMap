"""MoneyMap CLI."""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import typer

from money_map.app.api import export_bundle, plan_variant, recommend_variants, validate_data
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


def _format_report(report: dict) -> str:
    lines = [
        "validation report",
        f"status: {report['status']}",
        f"dataset_version: {report['dataset_version']}",
        f"reviewed_at: {report['reviewed_at']}",
        f"stale: {report['stale']}",
        f"staleness_policy_days: {report['staleness']['rulepack'].get('threshold_days')}",
        f"fatals: {len(report['fatals'])}",
        f"warns: {len(report['warns'])}",
    ]
    if report["fatals"]:
        lines.append("FATALS:")
        lines.extend([f"- {fatal}" for fatal in report["fatals"]])
    if report["warns"]:
        lines.append("WARNS:")
        lines.extend([f"- {warn}" for warn in report["warns"]])
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


def _abort_on_fatals(report: dict) -> None:
    if report["fatals"]:
        typer.echo("Validation failed with fatals:")
        for fatal in report["fatals"]:
            typer.echo(f"- {fatal}")
        raise typer.Exit(code=1)


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
    report = validate_data(data_dir)
    typer.echo(_format_report(report))
    if report["fatals"]:
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
    report = validate_data(data_dir)
    _abort_on_fatals(report)
    result = recommend_variants(profile, objective=objective, top_n=top, data_dir=data_dir)
    output_format = output_format.strip().lower()
    if output_format not in {"text", "json"}:
        raise typer.BadParameter("format must be 'text' or 'json'")

    payload = {
        "objective": objective,
        "top_n": top,
        "recommendations": [
            {
                "variant_id": rec.variant.variant_id,
                "score": rec.score,
                "title": rec.variant.title,
                "pros": rec.pros,
                "cons": rec.cons,
                "stale": rec.stale,
                "staleness": rec.staleness,
                "legal_gate": rec.legal.legal_gate,
                "legal_checklist": rec.legal.checklist,
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
        typer.echo(f"{idx}. {rec.variant.variant_id} | score={rec.score:.2f} | {rec.variant.title}")
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
            {"diagnostics": result.diagnostics},
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


@app.command()
def plan(
    profile: str = typer.Option(..., "--profile", help="Path to profile YAML"),
    variant_id: str = typer.Option(..., "--variant-id", help="Variant ID"),
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
) -> None:
    """Generate a route plan for a selected variant."""
    report = validate_data(data_dir)
    _abort_on_fatals(report)
    try:
        plan_data = plan_variant(profile, variant_id, data_dir=data_dir)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(f"Plan for {plan_data.variant_id} with {len(plan_data.steps)} steps ready.")


@app.command()
def export(
    profile: str = typer.Option(..., "--profile", help="Path to profile YAML"),
    variant_id: str = typer.Option(..., "--variant-id", help="Variant ID"),
    out_dir: str = typer.Option("exports", "--out", help="Output directory"),
    data_dir: str = typer.Option("data", "--data-dir", "--data", help="Data directory"),
) -> None:
    """Export plan artifacts."""
    report = validate_data(data_dir)
    _abort_on_fatals(report)
    try:
        paths = export_bundle(profile, variant_id, out_dir=out_dir, data_dir=data_dir)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo("Exported:")
    typer.echo(f"- {paths['plan']}")
    typer.echo(f"- {paths['result']}")
    typer.echo(f"- {paths['profile']}")


@app.command()
def ui() -> None:
    """Launch the UI."""
    if importlib.util.find_spec("streamlit") is None:
        typer.echo('Streamlit is not installed. Install with: pip install -e ".[ui]"')
        raise typer.Exit(code=1)
    app_path = Path(__file__).resolve().parents[1] / "ui" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=False)


def main() -> None:
    _disable_network_if_requested()
    app()


if __name__ == "__main__":
    main()
