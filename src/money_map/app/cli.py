from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from money_map.core.load import load_app_data
from money_map.core.model import RecommendationResult, UserProfile
from money_map.core.plan import build_plan
from money_map.core.recommend import recommend
from money_map.core.validate import validate_app_data
from money_map.i18n import t
from money_map.render.json import to_json
from money_map.render.md import render_plan_md

app = typer.Typer(add_completion=False)
console = Console()


def _load_profile(path: Path) -> UserProfile:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return UserProfile.model_validate(data)


def _result_payload(result: RecommendationResult, lang: str, appdata) -> dict[str, Any]:
    translated: list[dict[str, Any]] = []
    variant_by_id = {variant.variant_id: variant for variant in appdata.variants}
    for item in result.ranked_variants:
        variant_id = item["variant_id"]
        variant = variant_by_id[variant_id]
        translated.append(
            {
                **item,
                "title": t(variant.title_key, lang),
                "summary": t(variant.summary_key, lang),
            }
        )
    return {"ranked_variants": translated, "diagnostics": result.diagnostics}


@app.command()
def validate(
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    lang: str = typer.Option("en", "--lang"),
) -> None:
    fatals, warns = validate_app_data(data_dir)

    table = Table(title=t("app.title", lang))
    table.add_column(t("cli.validate.level", lang))
    table.add_column(t("cli.validate.message", lang))
    for key, params in fatals:
        table.add_row(t("cli.validate.fatal", lang), t(key, lang, **params))
    for key, params in warns:
        table.add_row(t("cli.validate.warn", lang), t(key, lang, **params))

    console.print(table)
    if fatals:
        console.print(f"{t('cli.validate.fatal', lang)}: {len(fatals)}")
        raise typer.Exit(code=1)
    console.print(f"{t('cli.validate.ok', lang)} - {t('cli.validate.warn', lang)}: {len(warns)}")


@app.command()
def ui(
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    port: int = typer.Option(8501, "--port"),
) -> None:
    import subprocess

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "-m",
        "money_map.ui.app",
        "--server.port",
        str(port),
        "--",
        "--data-dir",
        str(data_dir),
    ]
    raise SystemExit(subprocess.call(command))


@app.command("recommend")
def recommend_cmd(
    profile: Path = typer.Option(Path("profiles/demo_fast_start.yaml"), "--profile"),
    top: int = typer.Option(10, "--top"),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    lang: str = typer.Option("en", "--lang"),
) -> None:
    appdata = load_app_data(data_dir)
    user_profile = _load_profile(profile)
    result = recommend(user_profile, appdata, top)
    payload = _result_payload(result, lang, appdata)
    console.print_json(json.dumps(payload, ensure_ascii=False))


@app.command()
def export(
    profile: Path = typer.Option(Path("profiles/demo_fast_start.yaml"), "--profile"),
    out: Path = typer.Option(Path("exports"), "--out"),
    data_dir: Path = typer.Option(Path("data"), "--data-dir"),
    lang: str = typer.Option("en", "--lang"),
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    appdata = load_app_data(data_dir)
    user_profile = _load_profile(profile)

    result = recommend(user_profile, appdata, top_n=10)
    payload = _result_payload(result, lang, appdata)
    selected_variant_id = payload["ranked_variants"][0]["variant_id"]
    plan = build_plan(selected_variant_id, user_profile, appdata)

    profile_path = out / "profile.yaml"
    result_path = out / "result.json"
    plan_path = out / "plan.md"

    with profile_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(user_profile.model_dump(), handle, sort_keys=True)

    with result_path.open("w", encoding="utf-8") as handle:
        handle.write(to_json(payload))

    with plan_path.open("w", encoding="utf-8") as handle:
        handle.write(render_plan_md(plan))

    console.print(t("cli.export.done", lang, path=str(out)))
