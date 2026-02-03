"""Render plan as Markdown."""

from __future__ import annotations

from money_map.core.model import RoutePlan


def render_plan_md(plan: RoutePlan) -> str:
    lines = [
        "# MoneyMap Plan",
        f"Variant: {plan.variant_id}",
        "",
        "## Steps",
    ]
    for idx, step in enumerate(plan.steps, start=1):
        lines.append(f"{idx}. **{step.title}** — {step.detail}")

    lines.extend(["", "## Artifacts"])
    for artifact in plan.artifacts:
        lines.append(f"- {artifact}")

    lines.extend(["", "## 4-Week Outline"])
    for week, items in plan.week_plan.items():
        lines.append(f"- {week.replace('_', ' ').title()}: {', '.join(items)}")

    lines.extend(["", "## Compliance"])
    lines.append(f"Legal gate: **{plan.legal_gate}**")
    for item in plan.compliance:
        lines.append(f"- {item}")

    lines.extend(["", "## Staleness"])
    rulepack = plan.staleness.get("rulepack", {})
    variant = plan.staleness.get("variant", {})
    if rulepack:
        lines.append(
            f"- Rulepack: {rulepack.get('message', 'n/a')} "
            f"(severity: {rulepack.get('severity', 'n/a')})"
        )
    if variant:
        lines.append(
            f"- Variant: {variant.get('message', 'n/a')} "
            f"(severity: {variant.get('severity', 'n/a')})"
        )

    return "\n".join(lines) + "\n"
