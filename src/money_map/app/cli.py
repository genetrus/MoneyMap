from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import typer
except ImportError:  # pragma: no cover - optional dependency
    typer = None

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover - optional dependency
    Console = None
    Table = None

from money_map.core.data_dictionary import generate_data_dictionary
from money_map.core.load import load_app_data, load_yaml
from money_map.core.model import RecommendationResult, UserProfile
from money_map.core.plan import build_plan
from money_map.core.recommend import recommend
from money_map.core.validate import validate_app_data
from money_map.core.yaml_utils import dump_yaml
from money_map.i18n import t
from money_map.i18n.audit import audit_i18n, print_audit_report
from money_map.i18n.i18n import SUPPORTED_LANGS
from money_map.i18n.locale import format_percent
from money_map.render.json import to_json
from money_map.render.md import render_checklist_md, render_plan_md

if typer:
    app = typer.Typer(add_completion=False)
else:
    app = None

console = Console() if Console else None


def _load_profile(path: Path) -> UserProfile:
    data = load_yaml(path)
    return UserProfile.model_validate(data)


def _translate_list(items: list[str], lang: str) -> list[str]:
    return [t(item, lang) for item in items]


def _result_payload(result: RecommendationResult, lang: str, appdata) -> dict[str, Any]:
    translated: list[dict[str, Any]] = []
    variant_by_id = {variant.variant_id: variant for variant in appdata.variants}
    for item in result.ranked_variants:
        item_payload = item.model_dump() if hasattr(item, "model_dump") else item
        variant_id = item_payload["variant_id"]
        variant = variant_by_id[variant_id]
        translated.append(
            {
                **item_payload,
                "title": t(variant.title_key, lang),
                "summary": t(variant.summary_key, lang),
                "pros": _translate_list(item_payload.get("pros", []), lang),
                "cons": _translate_list(item_payload.get("cons", []), lang),
                "blockers": _translate_list(item_payload.get("blockers", []), lang),
                "assumptions": _translate_list(item_payload.get("assumptions", []), lang),
            }
        )
    return {"ranked_variants": translated, "diagnostics": result.diagnostics}


def _dump_yaml(data: dict[str, Any]) -> str:
    return dump_yaml(data)


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


def i18n_audit_command(
    data_dir: Path,
    lang: str,
    langs: list[str],
    strict: bool,
    strict_dataset: bool,
    report_unused: bool,
) -> int:
    fatals, warns = audit_i18n(
        data_dir, langs, strict_dataset=strict_dataset, report_unused=report_unused
    )
    print_audit_report(fatals, warns, lang)
    if fatals and strict:
        return 1
    return 0


def data_docs_command(data_dir: Path, out: Path) -> int:
    generate_data_dictionary(data_dir, out)
    return 0


def preset_list_command(data_dir: Path, lang: str) -> int:
    appdata = load_app_data(data_dir)
    if Table and console:
        table = Table(title=t("cli.preset.list_header", lang))
        table.add_column(t("cli.preset.id", lang))
        table.add_column(t("cli.preset.title", lang))
        table.add_column(t("cli.preset.summary", lang))
        table.add_column(t("cli.preset.weights", lang))
        for preset in appdata.presets:
            weights = ", ".join(
                [
                    f"{t('cli.preset.weight.feasibility', lang)} "
                    f"{format_percent(preset.weight_feasibility, lang)}",
                    f"{t('cli.preset.weight.economics', lang)} "
                    f"{format_percent(preset.weight_economics, lang)}",
                    f"{t('cli.preset.weight.legal', lang)} "
                    f"{format_percent(preset.weight_legal, lang)}",
                    f"{t('cli.preset.weight.fit', lang)} "
                    f"{format_percent(preset.weight_fit, lang)}",
                    f"{t('cli.preset.weight.staleness', lang)} "
                    f"{format_percent(preset.weight_staleness, lang)}",
                ]
            )
            table.add_row(
                preset.preset_id,
                t(preset.title_key, lang),
                t(preset.summary_key, lang),
                weights,
            )
        console.print(table)
        return 0
    for preset in appdata.presets:
        print(
            f"{preset.preset_id}: {t(preset.title_key, lang)} - "
            f"{t(preset.summary_key, lang)}"
        )
    return 0


def preset_show_command(preset_id: str, data_dir: Path, lang: str) -> int:
    appdata = load_app_data(data_dir)
    preset = next((item for item in appdata.presets if item.preset_id == preset_id), None)
    if preset is None:
        message = t("cli.preset.not_found", lang, preset_id=preset_id)
        if console:
            console.print(message)
        else:
            print(message)
        return 1
    weights = {
        t("cli.preset.weight.feasibility", lang): format_percent(
            preset.weight_feasibility, lang
        ),
        t("cli.preset.weight.economics", lang): format_percent(
            preset.weight_economics, lang
        ),
        t("cli.preset.weight.legal", lang): format_percent(preset.weight_legal, lang),
        t("cli.preset.weight.fit", lang): format_percent(preset.weight_fit, lang),
        t("cli.preset.weight.staleness", lang): format_percent(
            preset.weight_staleness, lang
        ),
    }
    if Table and console:
        table = Table(title=t("cli.preset.show_header", lang))
        table.add_column(t("cli.preset.field", lang))
        table.add_column(t("cli.preset.value", lang))
        table.add_row(t("cli.preset.id", lang), preset.preset_id)
        table.add_row(t("cli.preset.title", lang), t(preset.title_key, lang))
        table.add_row(t("cli.preset.summary", lang), t(preset.summary_key, lang))
        for key, value in weights.items():
            table.add_row(key, value)
        if preset.constraints_profile_overrides is not None:
            table.add_row(
                t("cli.preset.constraints_override", lang),
                ", ".join(preset.constraints_profile_overrides),
            )
        if preset.sorting_policy:
            table.add_row(t("cli.preset.sorting_policy", lang), preset.sorting_policy)
        console.print(table)
        return 0
    print(f"{t('cli.preset.id', lang)}: {preset.preset_id}")
    print(f"{t('cli.preset.title', lang)}: {t(preset.title_key, lang)}")
    print(f"{t('cli.preset.summary', lang)}: {t(preset.summary_key, lang)}")
    for key, value in weights.items():
        print(f"{key}: {value}")
    return 0


def doctor_command(data_dir: Path, lang: str) -> int:
    checks: list[tuple[str, str, str]] = []
    status_rank = {"PASS": 0, "WARN": 1, "FAIL": 2}
    status_labels = {
        "PASS": t("cli.doctor.status.pass", lang),
        "WARN": t("cli.doctor.status.warn", lang),
        "FAIL": t("cli.doctor.status.fail", lang),
    }

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append((name, status, detail))

    if sys.version_info >= (3, 11):
        add_check(t("cli.doctor.python", lang), "PASS", sys.version.split()[0])
    else:
        add_check(t("cli.doctor.python", lang), "WARN", sys.version.split()[0])

    for module_name in ("yaml", "pydantic", "rich", "typer"):
        try:
            __import__(module_name)
            add_check(t("cli.doctor.dependency", lang), "PASS", module_name)
        except ImportError:
            status = "FAIL" if module_name in {"yaml", "pydantic"} else "WARN"
            add_check(t("cli.doctor.dependency", lang), status, module_name)

    if data_dir.exists():
        add_check(t("cli.doctor.data_dir", lang), "PASS", str(data_dir))
    else:
        add_check(t("cli.doctor.data_dir", lang), "FAIL", str(data_dir))

    exports_dir = data_dir.parent / "exports"
    try:
        exports_dir.mkdir(parents=True, exist_ok=True)
        test_path = exports_dir / ".doctor_write_test"
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink()
        add_check(t("cli.doctor.exports_dir", lang), "PASS", str(exports_dir))
    except OSError as exc:
        add_check(t("cli.doctor.exports_dir", lang), "FAIL", str(exc))

    fatals, warns = validate_app_data(data_dir, strict=True)
    if fatals:
        add_check(
            t("cli.doctor.validate", lang),
            "FAIL",
            t("cli.doctor.found", lang, count=len(fatals)),
        )
    elif warns:
        add_check(
            t("cli.doctor.validate", lang),
            "WARN",
            t("cli.doctor.found", lang, count=len(warns)),
        )
    else:
        add_check(t("cli.doctor.validate", lang), "PASS", t("cli.doctor.ok", lang))

    i18n_fatals, i18n_warns = audit_i18n(
        data_dir, SUPPORTED_LANGS, strict_dataset=True
    )
    if i18n_fatals:
        add_check(
            t("cli.doctor.i18n", lang),
            "FAIL",
            t("cli.doctor.found", lang, count=len(i18n_fatals)),
        )
    elif i18n_warns:
        add_check(
            t("cli.doctor.i18n", lang),
            "WARN",
            t("cli.doctor.found", lang, count=len(i18n_warns)),
        )
    else:
        add_check(t("cli.doctor.i18n", lang), "PASS", t("cli.doctor.ok", lang))

    profile_path = data_dir.parent / "profiles" / "demo_fast_start.yaml"
    try:
        profile = _load_profile(profile_path)
        appdata = load_app_data(data_dir)
        _ = recommend(profile, appdata, top_n=3)
        add_check(t("cli.doctor.recommend", lang), "PASS", profile_path.name)
    except Exception as exc:  # pragma: no cover - safety
        add_check(t("cli.doctor.recommend", lang), "FAIL", str(exc))

    if Table and console:
        table = Table(title=t("cli.doctor.header", lang))
        table.add_column(t("cli.doctor.check", lang))
        table.add_column(t("cli.doctor.status", lang))
        table.add_column(t("cli.doctor.detail", lang))
        for name, status, detail in checks:
            table.add_row(name, status_labels.get(status, status), detail)
        console.print(table)
    else:
        for name, status, detail in checks:
            label = status_labels.get(status, status)
            print(f"{name}: {label} - {detail}")

    worst_status = max(checks, key=lambda item: status_rank[item[1]])[1]
    summary_key = {
        "PASS": "cli.doctor.summary_pass",
        "WARN": "cli.doctor.summary_warn",
        "FAIL": "cli.doctor.summary_fail",
    }[worst_status]
    message = t(summary_key, lang)
    if console:
        console.print(message)
    else:
        print(message)
    return 0 if worst_status != "FAIL" else 1

def _print_recommendations(result: RecommendationResult, appdata, lang: str) -> None:
    variant_by_id = {variant.variant_id: variant for variant in appdata.variants}
    if Table and console:
        table = Table(title=t("app.title", lang))
        table.add_column(t("cli.recommend.rank", lang))
        table.add_column(t("cli.recommend.title", lang))
        table.add_column(t("cli.recommend.score", lang))
        table.add_column(t("cli.recommend.top_pro", lang))
        table.add_column(t("cli.recommend.top_blocker", lang))
        for index, item in enumerate(result.ranked_variants, start=1):
            variant = variant_by_id[item.variant_id]
            top_pro = item.pros[0] if item.pros else t("cli.recommend.none", lang)
            top_blocker = (
                item.blockers[0] if item.blockers else t("cli.recommend.none", lang)
            )
            table.add_row(
                str(index),
                t(variant.title_key, lang),
                format_percent(item.score_total, lang),
                t(top_pro, lang),
                t(top_blocker, lang),
            )
        console.print(table)
        return

    for index, item in enumerate(result.ranked_variants, start=1):
        variant = variant_by_id[item.variant_id]
        top_pro = item.pros[0] if item.pros else t("cli.recommend.none", lang)
        top_blocker = item.blockers[0] if item.blockers else t("cli.recommend.none", lang)
        print(
            f"{index}. {t(variant.title_key, lang)} | "
            f"{t('cli.recommend.score', lang)}: {format_percent(item.score_total, lang)} | "
            f"{t('cli.recommend.top_pro', lang)}: {t(top_pro, lang)} | "
            f"{t('cli.recommend.top_blocker', lang)}: {t(top_blocker, lang)}"
        )


def recommend_command(
    profile: Path, top: int, data_dir: Path, lang: str, explain: bool
) -> int:
    appdata = load_app_data(data_dir)
    user_profile = _load_profile(profile)
    result = recommend(user_profile, appdata, top)
    _print_recommendations(result, appdata, lang)
    if explain:
        payload = _result_payload(result, lang, appdata)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def export_command(
    profile: Path, out: Path, data_dir: Path, lang: str, today: str | None = None
) -> int:
    out.mkdir(parents=True, exist_ok=True)
    appdata = load_app_data(data_dir)
    user_profile = _load_profile(profile)

    today_date = None
    if today:
        try:
            today_date = datetime.fromisoformat(today).date()
        except ValueError:
            today_date = None

    result = recommend(user_profile, appdata, top_n=10, today=today_date)
    payload = _result_payload(result, lang, appdata)
    selected_variant_id = payload["ranked_variants"][0]["variant_id"]
    plan = build_plan(selected_variant_id, user_profile, appdata, today=today_date)

    profile_path = out / "profile.yaml"
    result_path = out / "result.json"
    plan_path = out / "plan.md"
    checklist_path = out / "checklist.md"

    with profile_path.open("w", encoding="utf-8") as handle:
        handle.write(_dump_yaml(user_profile.model_dump()))

    with result_path.open("w", encoding="utf-8") as handle:
        handle.write(to_json(payload))

    with plan_path.open("w", encoding="utf-8") as handle:
        handle.write(render_plan_md(plan, lang))

    with checklist_path.open("w", encoding="utf-8") as handle:
        handle.write(render_checklist_md(plan.compliance_checklist, lang))

    message = t("cli.export.done", lang, path=str(out))
    if console:
        console.print(message)
    else:
        print(message)
    return 0


def ui_command(data_dir: Path, port: int, lang: str) -> int:
    _ = lang
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
        lang: str = typer.Option("en", "--lang", "-l"),
        strict: bool = typer.Option(False, "--strict"),
    ) -> None:
        raise typer.Exit(code=validate_command(data_dir, lang, strict))

    @app.command()
    def ui(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        port: int = typer.Option(8501, "--port"),
        lang: str = typer.Option("en", "--lang", "-l"),
    ) -> None:
        raise typer.Exit(code=ui_command(data_dir, port, lang))

    @app.command("recommend")
    def recommend_cmd(
        profile: Path = typer.Option(Path("profiles/demo_fast_start.yaml"), "--profile"),
        top: int = typer.Option(10, "--top"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang", "-l"),
        explain: bool = typer.Option(False, "--explain"),
    ) -> None:
        raise typer.Exit(code=recommend_command(profile, top, data_dir, lang, explain))

    @app.command()
    def export(
        profile: Path = typer.Option(Path("profiles/demo_fast_start.yaml"), "--profile"),
        out: Path = typer.Option(Path("exports"), "--out"),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang", "-l"),
        today: str | None = typer.Option(None, "--today"),
    ) -> None:
        raise typer.Exit(code=export_command(profile, out, data_dir, lang, today))

    @app.command("doctor")
    def doctor(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang", "-l"),
    ) -> None:
        raise typer.Exit(code=doctor_command(data_dir, lang))

    preset_app = typer.Typer(help="preset tools")
    app.add_typer(preset_app, name="preset")

    @preset_app.command("list")
    def preset_list(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang", "-l"),
    ) -> None:
        raise typer.Exit(code=preset_list_command(data_dir, lang))

    @preset_app.command("show")
    def preset_show(
        preset_id: str = typer.Argument(...),
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang", "-l"),
    ) -> None:
        raise typer.Exit(code=preset_show_command(preset_id, data_dir, lang))

    i18n_app = typer.Typer(help="i18n tools")
    app.add_typer(i18n_app, name="i18n")

    @i18n_app.command("audit")
    def i18n_audit(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        lang: str = typer.Option("en", "--lang"),
        langs: str = typer.Option("en,de,fr,es,pl,ru", "--langs"),
        strict: bool = typer.Option(False, "--strict"),
        strict_dataset: bool = typer.Option(False, "--strict-dataset"),
        report_unused: bool = typer.Option(False, "--report-unused"),
    ) -> None:
        raise typer.Exit(
            code=i18n_audit_command(
                data_dir,
                lang,
                [item for item in langs.split(",") if item.strip()],
                strict,
                strict_dataset,
                report_unused,
            )
        )

    data_app = typer.Typer(help="data tools")
    app.add_typer(data_app, name="data")

    @data_app.command("docs")
    def data_docs(
        data_dir: Path = typer.Option(Path("data"), "--data-dir"),
        out: Path = typer.Option(Path("docs/data_dictionary.md"), "--out"),
    ) -> None:
        raise typer.Exit(code=data_docs_command(data_dir, out))


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
    recommend_parser.add_argument("--explain", action="store_true")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--profile", default="profiles/demo_fast_start.yaml")
    export_parser.add_argument("--out", default="exports")
    export_parser.add_argument("--data-dir", default="data")
    export_parser.add_argument("--today")

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--data-dir", default="data")

    preset_parser = subparsers.add_parser("preset")
    preset_subparsers = preset_parser.add_subparsers(dest="preset_command")
    preset_list_parser = preset_subparsers.add_parser("list")
    preset_list_parser.add_argument("--data-dir", default="data")
    preset_show_parser = preset_subparsers.add_parser("show")
    preset_show_parser.add_argument("preset_id")
    preset_show_parser.add_argument("--data-dir", default="data")

    i18n_parser = subparsers.add_parser("i18n")
    i18n_subparsers = i18n_parser.add_subparsers(dest="i18n_command")
    audit_parser = i18n_subparsers.add_parser("audit")
    audit_parser.add_argument("--data-dir", default="data")
    audit_parser.add_argument("--lang", default="en")
    audit_parser.add_argument("--langs", default="en,de,fr,es,pl,ru")
    audit_parser.add_argument("--strict", action="store_true")
    audit_parser.add_argument("--strict-dataset", action="store_true")
    audit_parser.add_argument("--report-unused", action="store_true")

    data_parser = subparsers.add_parser("data")
    data_subparsers = data_parser.add_subparsers(dest="data_command")
    docs_parser = data_subparsers.add_parser("docs")
    docs_parser.add_argument("--data-dir", default="data")
    docs_parser.add_argument("--out", default="docs/data_dictionary.md")

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
        return ui_command(Path(args.data_dir), args.port, args.lang)
    if args.command == "recommend":
        return recommend_command(
            Path(args.profile),
            args.top,
            Path(args.data_dir),
            args.lang,
            getattr(args, "explain", False),
        )
    if args.command == "export":
        return export_command(
            Path(args.profile),
            Path(args.out),
            Path(args.data_dir),
            args.lang,
            getattr(args, "today", None),
        )
    if args.command == "doctor":
        return doctor_command(Path(args.data_dir), args.lang)
    if args.command == "preset" and args.preset_command == "list":
        return preset_list_command(Path(args.data_dir), args.lang)
    if args.command == "preset" and args.preset_command == "show":
        return preset_show_command(args.preset_id, Path(args.data_dir), args.lang)
    if args.command == "i18n" and args.i18n_command == "audit":
        return i18n_audit_command(
            Path(args.data_dir),
            args.lang,
            [item for item in args.langs.split(",") if item.strip()],
            args.strict,
            args.strict_dataset,
            getattr(args, "report_unused", False),
        )
    if args.command == "data" and args.data_command == "docs":
        return data_docs_command(Path(args.data_dir), Path(args.out))

    parser.print_help()
    return 0
