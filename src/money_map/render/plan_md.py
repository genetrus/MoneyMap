"""Render plan as Markdown (Plan Template v1)."""

from __future__ import annotations

from money_map.core.model import RoutePlan


def _ensure_minimum_quotas(plan: RoutePlan) -> None:
    if len(plan.steps) < 10:
        raise ValueError("Plan must contain at least 10 steps.")
    if len(plan.artifacts) < 3:
        raise ValueError("Plan must contain at least 3 artifacts.")
    if not plan.compliance:
        raise ValueError("Plan must include compliance checklist items.")


def _variant_staleness_status(plan: RoutePlan) -> str:
    rulepack = plan.staleness.get("rulepack", {})
    variant = plan.staleness.get("variant", {})
    severities = {str(rulepack.get("severity", "ok")), str(variant.get("severity", "ok"))}
    if "fatal" in severities:
        return "hard"
    if "warn" in severities:
        return "warn"
    return "fresh"


def render_plan_md(plan: RoutePlan) -> str:
    _ensure_minimum_quotas(plan)

    staleness_status = _variant_staleness_status(plan)

    lines = [
        f"# Plan: {plan.variant_id}  ·  {plan.variant_id}",
        "",
        "> ⚠️ **Disclaimer:** money/time values are ranges and estimates, not guarantees.",
        "> Legal/Compliance is a verification checklist, not legal advice.",
        "",
        "---",
        "",
        "## 0) Metadata",
        "- **Country:** DE",
        "- **Generated at:** unknown",
        "- **Dataset:** unknown · **Schema:** unknown",
        "- **Rulepack:** DE @ unknown",
        f"- **Staleness:** {staleness_status}",
        "- **Profile hash:** unknown",
        "- **Objective preset:** unknown",
        f"- **Legal gate:** {plan.legal_gate}",
        "- **Confidence:** unknown",
        "",
        "---",
        "",
        "## 1) Executive summary",
        f"**Selected variant:** {plan.variant_id}",
        "**Short:** route generated from deterministic local data.",
        "",
        "### Why this variant (exactly 3)",
        "- Deterministic offline-compatible route",
        "- Includes compliance and staleness guardrails",
        "- Keeps weekly milestones explicit",
        "",
        "### What can block (1–2)",
        "- Legal gate may require manual checks",
        "- Economics are only estimated ranges",
        "",
        "---",
        "",
        "## 2) Preconditions & Blockers (feasibility)",
        "### Feasibility status",
        "- **Status:** feasible_with_prep",
        "- **Prep estimate:** unknown",
        "",
        "### Key blockers (up to 3)",
    ]
    for item in plan.compliance[:3]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "### Minimum floors",
            "- **Language:** unknown",
            "- **Time/week:** unknown",
            "- **Assets:** unknown",
            "- **Other:** unknown",
            "",
            "### Prep steps",
            "- [ ] Review feasibility constraints",
            "- [ ] Prepare baseline assets",
            "- [ ] Verify legal prerequisites",
            "",
            "---",
            "",
            "## 3) Targets & Success criteria (4 weeks)",
            "- **Week 1:** setup complete",
            "- **Week 2:** first outreach executed",
            "- **Week 3:** first feedback loop completed",
            "- **Week 4:** checkpoint and decision logged",
            "",
            "**Minimum KPI:**",
            "- 10 outreach actions/week",
            "- weekly economics tracking updated",
            "- compliance checklist reviewed",
            "",
            "---",
            "",
            "## 4) Required artifacts (minimum 3)",
        ]
    )
    for artifact in plan.artifacts:
        lines.append(f"- [ ] **Artifact:** {artifact} — prepared — available in export bundle")

    lines.extend(["", "---", "", "## 5) Step-by-step checklist — minimum 10"])
    for idx, step in enumerate(plan.steps, start=1):
        lines.append(
            f"- [ ] **S{idx}:** {step.title} — {step.detail} — eta: unknown — depends: none"
        )

    lines.extend(["", "---", "", "## 6) 4-week plan (Week 1–4)"])
    for week, items in plan.week_plan.items():
        lines.append(f"### {week}")
        lines.append(f"**Outcome:** {', '.join(items[:2]) if items else 'n/a'}")
        lines.append(f"**Tasks:** {', '.join(items) if items else 'n/a'}")
        lines.append("**Checkpoint:** logged")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 7) Compliance & Legal checks",
            f"> **Gate:** {plan.legal_gate}",
            "> If staleness is warn/hard, re-check all legal assumptions.",
            "",
            "### Checklist",
        ]
    )
    for item in plan.compliance:
        lines.append(f"- [ ] {item}")

    lines.extend(
        [
            "",
            "### Compliance kits",
            "- **Tax basics:** see checklist",
            "- **Invoicing:** see checklist",
            "- **Insurance:** see checklist",
            "- **Platform terms:** see checklist",
            "",
            "---",
            "",
            "## 8) Economics & Tracking (estimate, not guarantee)",
            "- **Time to first money:** unknown",
            "- **Typical net/month:** unknown",
            "- **Costs:** fixed unknown · variable unknown",
            "- **Volatility:** unknown · **Ceiling:** unknown · **Confidence:** unknown",
            "",
            "### Tracking",
            "- [ ] Keep weekly income/expense/time log",
            "- [ ] Recalculate net each week",
            "- [ ] Apply a decision rule at week-end review",
            "",
            "---",
            "",
            "## 9) Risks & Mitigations (minimum 5)",
            "| Risk | Likelihood | Impact | Mitigation | Trigger |",
            "|---|---:|---:|---|---|",
            "| Legal mismatch | M | H | Re-check legal gate | checklist gap |",
            "| Low demand | M | M | Increase outreach | no replies |",
            "| Time overrun | M | M | Reduce scope | missed milestones |",
            "| Cost creep | L | M | Cap weekly spend | budget drift |",
            "| Data staleness | M | M | Refresh assumptions | stale warning |",
            "",
            "---",
            "",
            "## 10) Decision points & Fallbacks",
            "### Decision points",
            "- **DP1:** if no traction by week 2 -> adjust offer",
            "- **DP2:** if legal uncertainty appears -> pause and verify",
            "",
            "### Fallback variants",
            "- **Alt A:** de.fast.freelance_writer — lower setup friction",
            "- **Alt B:** de.local.errand_helper — local quick-start path",
            "",
            "---",
            "",
            "## Appendix A) Evidence & Staleness",
        ]
    )

    rulepack = plan.staleness.get("rulepack", {})
    variant = plan.staleness.get("variant", {})
    lines.append(f"- Variant reviewed_at: {variant.get('age_days', 'unknown')} days age")
    lines.append(
        "- Rulepack reviewed_at: "
        + (
            f"{rulepack.get('age_days')} days age"
            if rulepack.get("age_days") is not None
            else "unknown"
        )
    )
    lines.append(
        f"- Staleness policy: warn_after={rulepack.get('warn_after_days', 'n/a')}d, "
        f"hard_after={rulepack.get('hard_after_days', 'n/a')}d"
    )
    lines.append("- Notes: generated from deterministic local rules and data.")

    return "\n".join(lines) + "\n"
