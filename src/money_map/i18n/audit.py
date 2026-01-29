from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover - optional dependency
    Console = None
    Table = None

from money_map.core.load import load_app_data
from money_map.i18n.i18n import SUPPORTED_LANGS, load_lang


CORE_KEYS = [
    "app.title",
    "nav.data_status",
    "nav.profile",
    "nav.recommendations",
    "nav.plan",
    "nav.export",
    "nav.data_explorer",
    "common.run_validate",
    "common.recommend",
    "common.export",
    "common.language",
    "cli.validate.ok",
    "cli.validate.fatal",
    "cli.validate.warn",
    "cli.validate.level",
    "cli.validate.message",
    "cli.i18n.header",
    "cli.i18n.lang",
    "cli.i18n.missing_keys",
    "cli.i18n.severity",
    "cli.i18n.none",
    "ui.data_status.dataset_version",
    "ui.data_status.reviewed_at",
    "ui.data_status.stale_warning",
    "ui.profile.header",
    "ui.reco.header",
    "ui.plan.header",
    "ui.export.header",
    "ui.plan.no_selection",
    "ui.profile.country",
    "ui.profile.time_hours",
    "ui.profile.capital",
    "ui.profile.language_level",
    "ui.profile.skills",
    "ui.profile.assets",
    "ui.profile.constraints",
    "ui.profile.objective_preset",
    "ui.profile.save",
    "ui.profile.saved",
    "ui.profile.upload",
    "ui.profile.loaded",
    "ui.common.load_profile_first",
    "ui.reco.objective_preset",
    "ui.reco.select",
    "ui.reco.reality_check",
    "ui.reco.blockers",
    "ui.reco.fixes",
    "ui.export.download_profile",
    "ui.export.download_result",
    "ui.export.download_plan",
    "ui.data_explorer.header",
    "ui.data_explorer.files_header",
    "ui.data_explorer.entities_header",
    "ui.data_explorer.validation_header",
    "ui.data_explorer.i18n_header",
    "ui.data_explorer.run_audit",
    "ui.data_explorer.run_validate",
    "ui.data_explorer.entity_type",
    "ui.data_explorer.entity_id",
    "ui.data_explorer.entity_details",
    "ui.data_explorer.file",
    "ui.data_explorer.exists",
    "ui.data_explorer.count",
    "ui.data_explorer.validation_fatals",
    "ui.data_explorer.validation_warns",
    "ui.data_explorer.i18n_missing",
]


@dataclass(frozen=True)
class MissingKey:
    lang: str
    severity: str
    key: str


def _normalize_langs(langs: Iterable[str]) -> list[str]:
    normalized = []
    for lang in langs:
        code = lang.strip().lower()
        if not code:
            continue
        if code in SUPPORTED_LANGS and code not in normalized:
            normalized.append(code)
    if not normalized:
        return SUPPORTED_LANGS
    return normalized


def _collect_dataset_keys(data_dir: Path) -> list[str]:
    appdata = load_app_data(data_dir)
    keys = set()
    for taxonomy in appdata.taxonomy:
        keys.add(taxonomy.title_key)
    for cell in appdata.cells:
        keys.add(cell.title_key)
    for variant in appdata.variants:
        keys.add(variant.title_key)
        keys.add(variant.summary_key)
    for item in appdata.skills:
        keys.add(item.title_key)
    for item in appdata.assets:
        keys.add(item.title_key)
    for item in appdata.constraints:
        keys.add(item.title_key)
    for item in appdata.objectives:
        keys.add(item.title_key)
    for item in appdata.risks:
        keys.add(item.title_key)
    for rulepack in appdata.rulepacks.values():
        for rule in rulepack.rules:
            keys.add(rule.title_key)
            keys.add(rule.summary_key)
        for kit in rulepack.compliance_kits:
            keys.add(kit.title_key)
            keys.add(kit.summary_key)
    return sorted(keys)


def audit_i18n(
    data_dir: Path,
    langs: Iterable[str] | None = None,
    strict_dataset: bool = False,
) -> tuple[list[MissingKey], list[MissingKey]]:
    lang_list = _normalize_langs(langs or SUPPORTED_LANGS)
    dataset_keys = _collect_dataset_keys(data_dir)
    fatals: list[MissingKey] = []
    warns: list[MissingKey] = []

    for lang in lang_list:
        translations = load_lang(lang)
        for key in CORE_KEYS:
            if key not in translations:
                fatals.append(MissingKey(lang=lang, severity="FATAL", key=key))
        for key in dataset_keys:
            if key not in translations:
                if lang == "en" or strict_dataset:
                    fatals.append(MissingKey(lang=lang, severity="FATAL", key=key))
                else:
                    warns.append(MissingKey(lang=lang, severity="WARN", key=key))

    fatals.sort(key=lambda item: (item.lang, item.key))
    warns.sort(key=lambda item: (item.lang, item.key))
    return fatals, warns


def print_audit_report(
    fatals: list[MissingKey], warns: list[MissingKey], lang: str
) -> None:
    if Table and Console:
        console = Console()
        table = Table(title=load_lang(lang).get("cli.i18n.header", "I18N Audit"))
        table.add_column(load_lang(lang).get("cli.i18n.lang", "Lang"))
        table.add_column(load_lang(lang).get("cli.i18n.severity", "Severity"))
        table.add_column(load_lang(lang).get("cli.i18n.missing_keys", "Missing keys"))
        entries = [*fatals, *warns]
        if not entries:
            table.add_row("-", "-", load_lang(lang).get("cli.i18n.none", "None"))
        else:
            for entry in entries:
                table.add_row(entry.lang, entry.severity, entry.key)
        console.print(table)
        return
    entries = [*fatals, *warns]
    if not entries:
        print(load_lang(lang).get("cli.i18n.none", "None"))
        return
    for entry in entries:
        print(f"{entry.lang} {entry.severity}: {entry.key}")
