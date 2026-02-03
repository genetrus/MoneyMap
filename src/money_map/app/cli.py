"""MoneyMap CLI."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import typer

from money_map.app.api import export_bundle, plan_variant, recommend_variants, validate_data

app = typer.Typer(help="MoneyMap CLI.")


def _format_report(report: dict) -> str:
    lines = [
        "validation report",
        f"status: {report['status']}",
        f"dataset_version: {report['dataset_version']}",
        f"reviewed_at: {report['reviewed_at']}",
        f"stale: {report['stale']}",
        f"fatals: {len(report['fatals'])}",
        f"warns: {len(report['warns'])}",
    ]
    if report["fatals"]:
        lines.append("FATALS:")
        lines.extend([f"- {fatal}" for fatal in report["fatals"]])
    if report["warns"]:
        lines.append("WARNS:")
        lines.extend([f"- {warn}" for warn in report["warns"]])
    return "\n".join(lines)


@app.command()
def validate(data_dir: str = "data") -> None:
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
    data_dir: str = typer.Option("data", "--data", help="Data directory"),
) -> None:
    """Recommend top variants."""
    result = recommend_variants(profile, objective=objective, top_n=top, data_dir=data_dir)
    for idx, rec in enumerate(result.ranked_variants, start=1):
        typer.echo(f"{idx}. {rec.variant.variant_id} | score={rec.score:.2f} | {rec.variant.title}")
        typer.echo(f"   Pros: {'; '.join(rec.pros)}")
        if rec.cons:
            typer.echo(f"   Cons: {'; '.join(rec.cons)}")
    typer.echo(json.dumps({"diagnostics": result.diagnostics}, ensure_ascii=False, indent=2))


@app.command()
def plan(
    profile: str = typer.Option(..., "--profile", help="Path to profile YAML"),
    variant_id: str = typer.Option(..., "--variant-id", help="Variant ID"),
    data_dir: str = typer.Option("data", "--data", help="Data directory"),
) -> None:
    """Generate a route plan for a selected variant."""
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
    data_dir: str = typer.Option("data", "--data", help="Data directory"),
) -> None:
    """Export plan artifacts."""
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
    app()


if __name__ == "__main__":
    main()
