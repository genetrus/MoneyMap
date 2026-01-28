from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import typer
except ImportError:  # pragma: no cover - optional dependency
    typer = None

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover - optional dependency
    Console = None
    Table = None

from money_map.core.load import load_app_data, load_yaml
from money_map.core.model import RecommendationResult, UserProfile
from money_map.core.plan import build_plan
from money_map.core.recommend import recommend
from money_map.core.validate import validate_app_data
from money_map.i18n import t
from money_map.render.json import to_json
from money_map.render.md import render_plan_md

if typer:
    app = typer.Typer(add_completion=False)
else:
    app = None

console = Console() if Console else None


def _load_profile(path: Path) -> UserProfile:
    data = load_yaml(path)
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


def _dump_yaml(data: dict[str, Any]) -> str:
    if yaml:
        return yaml.safe_dump(data, sort_keys=True)
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def _print_validation_report(
    fatals: list[tuple[str, dict]], warns: list[tuple[str, dict]], lang: str
) -> None:
    if Table and console:
        table = Table(title=t("app.title", lang))
        table.add_column(t("cli.validate.level", lang))
        table.add_column(t("cli.validate.message", lang))
        for key, params in fatals:
            table.add_row(t("cli.validate.fatal", lang), t(key, lang, **params))
        for key, params in warns:
            table.add_row(t("cli.validate.warn", lang), t(key, lang, **params))
        console.print(table)
    else:
        for key, params in fatals:
            print(f"{t('cli.validate.fatal', lang)}: {t(key, lang, **params)}")
        for key, params in warns:
            print(f"{t('cli.validate.warn', lang)}: {t(key, lang, **params)}")


def validate_command(data_dir: Path, lang: str, strict: bool) -> int:
    fatals, warns = validate_app_data(data_dir, strict=strict)
    _print_validation_report(fatals, warns, lang)
    if fatals:
        return 1
    if console:
        console.print(
            f"{t('cli.validate.ok', lang)} - {t('cli.validate.warn', lang)}: {len(warns)}"
        )
    else:
        print(f"{t('cli.validate.ok', lang)} - {t('cli.validate.warn', lang)}: {len(warns)}")
    return 0


def recommend_command(profile: Path, top: int, data_dir: Path, lang: str) -> int:
    appdata = load_app_data(data_dir)
    user_profile = _load_profile(profile)
    result = recommend(user_profile, appdata, top)
    payload = _result_payload(result, lang, appdata)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def export_command(profile: Path, out: Path, data_dir: Path, lang: str) -> int:
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
        handle.write(_dump_yaml(user_profile.model_dump()))

    with result_path.open("w", encoding="utf-8") as handle:
        handle.write(to_json(payload))

    with plan_path.open("w", encoding="utf-8") as handle:
        handle.write(render_plan_md(plan))

    message = t("cli.export.done", lang, path=str(out))
    if console:
        console.print(message)
    else:
        print(message)
    return 0


def ui_command(data_dir: Path, port: int) -> int:
    try:
        import streamlit  # noqa: F401
    except ImportError:
        print("Streamlit is not available. Install streamlit to run the UI.")
        return 1

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
    return subprocess.call(command)


if typer:

    @app.command()
    def validate(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang"),
        strict: bool = typer.Option(False, "--strict"),
    ) -> None:
        raise typer.Exit(code=validate_command(data_dir, lang, strict))

    @app.command()
    def ui(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        port: int = typer.Option(8501, "--port"),
    ) -> None:
        raise typer.Exit(code=ui_command(data_dir, port))

    @app.command("recommend")
    def recommend_cmd(
        profile: Path = typer.Option(Path("profiles/demo_fast_start.yaml"), "--profile"),
        top: int = typer.Option(10, "--top"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang"),
    ) -> None:
        raise typer.Exit(code=recommend_command(profile, top, data_dir, lang))

    @app.command()
    def export(
        profile: Path = typer.Option(Path("profiles/demo_fast_start.yaml"), "--profile"),
        out: Path = typer.Option(Path("exports"), "--out"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang"),
    ) -> None:
        raise typer.Exit(code=export_command(profile, out, data_dir, lang))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="money_map")
    parser.add_argument("--lang", default="en")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--data-dir", default="data")
    validate_parser.add_argument("--strict", action="store_true")

    ui_parser = subparsers.add_parser("ui")
    ui_parser.add_argument("--data-dir", default="data")
    ui_parser.add_argument("--port", type=int, default=8501)

    recommend_parser = subparsers.add_parser("recommend")
    recommend_parser.add_argument("--profile", default="profiles/demo_fast_start.yaml")
    recommend_parser.add_argument("--top", type=int, default=10)
    recommend_parser.add_argument("--data-dir", default="data")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--profile", default="profiles/demo_fast_start.yaml")
    export_parser.add_argument("--out", default="exports")
    export_parser.add_argument("--data-dir", default="data")

    return parser


def main(argv: list[str] | None = None) -> int:
    if typer and app is not None:
        try:
            app(prog_name="money_map", args=argv)
        except SystemExit as exc:
            return int(exc.code) if exc.code is not None else 0
        return 0

    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0

    if args.command == "validate":
        return validate_command(Path(args.data_dir), args.lang, args.strict)
    if args.command == "ui":
        return ui_command(Path(args.data_dir), args.port)
    if args.command == "recommend":
        return recommend_command(Path(args.profile), args.top, Path(args.data_dir), args.lang)
    if args.command == "export":
        return export_command(Path(args.profile), Path(args.out), Path(args.data_dir), args.lang)

    parser.print_help()
    return 0
