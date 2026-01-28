from __future__ import annotations

from money_map.core.model import RoutePlan


def render_plan_md(plan: RoutePlan) -> str:
    lines = [
        f"# Plan for {plan.selected_variant_id}",
        "",
        "## Steps",
    ]
    for step in plan.steps:
        lines.append(f"- {step.get('step')} ({step.get('status')})")
    lines.append("")
    lines.append("## 4-week plan")
    for week in plan.week_plan:
        lines.append(f"- Week {week.get('week')}: {week.get('focus')}")
    lines.append("")
    lines.append("## Compliance")
    lines.append("- Placeholder compliance checks")
    lines.append("")
    lines.append("## Disclaimers")
    lines.append("- Not legal advice")
    lines.append("- No income guarantees")
    return "\n".join(lines)
