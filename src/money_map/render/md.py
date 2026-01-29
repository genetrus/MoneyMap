from __future__ import annotations

from money_map.core.model import RoutePlan
from money_map.i18n import t
from money_map.i18n.locale import format_date, format_int


def _format_list(items: list[str], lang: str) -> list[str]:
    return [t(item, lang) for item in items]


def render_plan_md(plan: RoutePlan, lang: str) -> str:
    lines = [f"# {t('planner.heading.plan', lang)}", ""]
    lines.append(f"## {t('planner.heading.overview', lang)}")
    lines.append(
        f"- {t('planner.overview.goal', lang)}: "
        f"{t(plan.overview.get('goal_variant_key', ''), lang)}"
    )
    lines.append(
        f"- {t('planner.overview.time_budget', lang)}: "
        f"{format_int(plan.overview.get('time_hours_per_week', 0), lang)} "
        f"{t('planner.units.hours_per_week', lang)}"
    )
    constraints = plan.overview.get("constraints", [])
    if constraints:
        lines.append(
            f"- {t('planner.overview.constraints', lang)}: "
            f"{', '.join([t(item, lang) for item in constraints])}"
        )
    risk_level = plan.overview.get("risk_tolerance", "medium")
    lines.append(
        f"- {t('planner.overview.risk_tolerance', lang)}: "
        f"{t(f'profile.risk_tolerance.{risk_level}', lang)}"
    )
    lines.append("")

    lines.append(f"## {t('planner.heading.steps', lang)}")
    for step in plan.steps:
        lines.append(
            f"### {t(step.get('title_key', ''), lang)} "
            f"({t('planner.week_label', lang, week=step.get('week'))})"
        )
        lines.append(
            f"- {t('planner.estimated_hours', lang)}: "
            f"{format_int(step.get('estimated_hours', 0), lang)}"
        )
        lines.append(f"- {t('planner.actions', lang)}:")
        for action in _format_list(step.get("actions", []), lang):
            lines.append(f"  - {action}")
        lines.append(f"- {t('planner.outputs', lang)}:")
        for output in _format_list(step.get("outputs", []), lang):
            lines.append(f"  - {output}")
        checks = _format_list(step.get("checks", []), lang)
        if checks:
            lines.append(f"- {t('planner.checks', lang)}:")
            for check in checks:
                lines.append(f"  - {check}")
        lines.append("")

    lines.append(f"## {t('planner.heading.week_plan', lang)}")
    for week in plan.week_plan:
        lines.append(f"- {t(week.get('title_key', ''), lang)}")
        for task in _format_list(week.get("tasks", []), lang):
            lines.append(f"  - {task}")
    lines.append("")

    lines.append(f"## {t('planner.heading.compliance', lang)}")
    if plan.compliance_checklist:
        for item in _format_list(plan.compliance_checklist, lang):
            lines.append(f"- {item}")
    else:
        lines.append(f"- {t('planner.compliance.none', lang)}")
    lines.append("")

    lines.append(f"## {t('planner.heading.risks', lang)}")
    for risk in _format_list(plan.risks, lang):
        lines.append(f"- {risk}")
    lines.append("")

    lines.append(f"## {t('planner.heading.next_reviews', lang)}")
    for review in plan.next_reviews:
        lines.append(
            f"- {t(review.get('item_key', ''), lang)}: "
            f"{format_date(review.get('due_date'), lang)}"
        )
    lines.append("")

    lines.append(f"## {t('planner.heading.artifacts', lang)}")
    for artifact in plan.artifacts:
        lines.append(
            f"- {artifact.get('filename')}: {t(artifact.get('description_key', ''), lang)}"
        )
    lines.append("")

    lines.append(f"## {t('planner.heading.disclaimer', lang)}")
    lines.append(f"- {t('planner.disclaimer.legal', lang)}")
    lines.append(f"- {t('planner.disclaimer.income', lang)}")
    return "\n".join(lines)


def render_checklist_md(checklist: list[str], lang: str) -> str:
    lines = [f"# {t('planner.heading.checklist', lang)}", ""]
    if checklist:
        for item in _format_list(checklist, lang):
            lines.append(f"- {item}")
    else:
        lines.append(f"- {t('planner.compliance.none', lang)}")
    return "\n".join(lines)
