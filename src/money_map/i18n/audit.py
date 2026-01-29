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
    "cli.recommend.rank",
    "cli.recommend.title",
    "cli.recommend.score",
    "cli.recommend.top_pro",
    "cli.recommend.top_blocker",
    "cli.recommend.none",
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
    "ui.plan.overview",
    "ui.plan.week_plan",
    "ui.plan.compliance_checklist",
    "ui.plan.next_reviews",
    "ui.plan.artifacts",
    "ui.profile.country",
    "ui.profile.time_hours",
    "ui.profile.capital",
    "ui.profile.language_level",
    "ui.profile.skills",
    "ui.profile.assets",
    "ui.profile.constraints",
    "ui.profile.risk_tolerance",
    "ui.profile.horizon_months",
    "ui.profile.target_net_monthly",
    "ui.profile.preferred_modes",
    "ui.profile.objective_preset",
    "ui.profile.save",
    "ui.profile.saved",
    "ui.profile.upload",
    "ui.profile.loaded",
    "ui.common.load_profile_first",
    "ui.reco.objective_preset",
    "ui.reco.select",
    "ui.reco.score_total",
    "ui.reco.score_breakdown",
    "ui.reco.score.feasibility",
    "ui.reco.score.economics",
    "ui.reco.score.legal",
    "ui.reco.score.fit",
    "ui.reco.score.staleness",
    "ui.reco.pros",
    "ui.reco.cons",
    "ui.reco.blockers",
    "ui.reco.assumptions",
    "ui.reco.compliance",
    "ui.reco.regulated_level",
    "ui.reco.required_kits",
    "ui.reco.stale_warn",
    "ui.reco.stale_force",
    "ui.reco.none",
    "ui.export.download_profile",
    "ui.export.download_result",
    "ui.export.download_plan",
    "ui.export.download_checklist",
    "ui.data_explorer.header",
    "ui.data_explorer.files_header",
    "ui.data_explorer.entities_header",
    "ui.data_explorer.validation_header",
    "ui.data_explorer.i18n_header",
    "ui.data_explorer.run_audit",
    "ui.data_explorer.run_validate",
    "ui.data_explorer.tab_entities",
    "ui.data_explorer.tab_rulepacks",
    "ui.data_explorer.rulepacks_header",
    "ui.data_explorer.rulepack_country",
    "ui.data_explorer.kits_header",
    "ui.data_explorer.rules_header",
    "ui.data_explorer.entity_type",
    "ui.data_explorer.entity_id",
    "ui.data_explorer.entity_details",
    "ui.data_explorer.file",
    "ui.data_explorer.exists",
    "ui.data_explorer.count",
    "ui.data_explorer.validation_fatals",
    "ui.data_explorer.validation_warns",
    "ui.data_explorer.i18n_missing",
    "legal.regulated.none",
    "legal.regulated.light",
    "legal.regulated.medium",
    "legal.regulated.high",
    "profile.risk_tolerance.low",
    "profile.risk_tolerance.medium",
    "profile.risk_tolerance.high",
    "reason.feasibility.low_complexity",
    "reason.feasibility.prerequisites_met",
    "reason.feasibility.fast_time_to_first",
    "reason.feasibility.high_complexity",
    "reason.feasibility.missing_prerequisite",
    "reason.feasibility.slow_time_to_first",
    "reason.economics.capex_within",
    "reason.economics.capex_high",
    "reason.economics.meets_target",
    "reason.economics.below_target",
    "reason.legal.unregulated",
    "reason.legal.medium_regulated",
    "reason.legal.high_regulated",
    "reason.legal.required_kits",
    "reason.legal.force_check",
    "reason.legal.placeholder_rulepack",
    "reason.fit.preferred_mode",
    "reason.staleness.warn",
    "assumption.market_demand",
    "assumption.client_acquisition",
    "assumption.supplier_reliability",
    "assumption.platform_access",
    "assumption.community_engagement",
    "assumption.content_quality",
    "assumption.client_data_access",
    "planner.heading.plan",
    "planner.heading.overview",
    "planner.heading.steps",
    "planner.heading.week_plan",
    "planner.heading.compliance",
    "planner.heading.risks",
    "planner.heading.next_reviews",
    "planner.heading.artifacts",
    "planner.heading.disclaimer",
    "planner.heading.checklist",
    "planner.overview.goal",
    "planner.overview.time_budget",
    "planner.overview.constraints",
    "planner.overview.risk_tolerance",
    "planner.units.hours_per_week",
    "planner.week_label",
    "planner.estimated_hours",
    "planner.actions",
    "planner.outputs",
    "planner.checks",
    "planner.compliance.none",
    "planner.week1.title",
    "planner.week2.title",
    "planner.week3.title",
    "planner.week4.title",
    "planner.action.define_offer",
    "planner.action.check_compliance",
    "planner.action.setup_tools",
    "planner.action.pilot_offer",
    "planner.action.first_revenue_attempt",
    "planner.action.collect_feedback",
    "planner.action.scale_process",
    "planner.action.optimize_pricing",
    "planner.action.expand_channels",
    "planner.action.stabilize_ops",
    "planner.action.review_metrics",
    "planner.action.plan_next_steps",
    "planner.action.source_suppliers",
    "planner.action.outline_content",
    "planner.action.map_processes",
    "planner.action.seed_community",
    "planner.output.offer_sheet",
    "planner.output.compliance_checklist",
    "planner.output.pilot_log",
    "planner.output.feedback_log",
    "planner.output.scaling_plan",
    "planner.output.channel_log",
    "planner.output.review_summary",
    "planner.output.next_review_dates",
    "planner.review.legal",
    "planner.review.market",
    "planner.review.financials",
    "planner.artifact.plan_md",
    "planner.artifact.result_json",
    "planner.artifact.profile_yaml",
    "planner.artifact.checklist_md",
    "planner.risk.cash_flow",
    "planner.risk.compliance",
    "planner.disclaimer.legal",
    "planner.disclaimer.income",
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
        econ = variant.economics
        if isinstance(econ, dict):
            margin_key = econ.get("margin_notes_key")
        else:
            margin_key = econ.margin_notes_key if econ else None
        if margin_key:
            keys.add(margin_key)
        legal = variant.legal
        if isinstance(legal, dict):
            disclaimer_key = legal.get("disclaimers_key")
        else:
            disclaimer_key = legal.disclaimers_key if legal else None
        if disclaimer_key:
            keys.add(disclaimer_key)
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
            effects = rule.effects if isinstance(rule.effects, dict) else {}
            for checklist in effects.get("add_checklist", []) or []:
                keys.add(checklist)
        for kit in rulepack.compliance_kits:
            keys.add(kit.title_key)
            keys.add(kit.summary_key)
            for checklist in kit.checklist:
                keys.add(checklist)
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
