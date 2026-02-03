"""Plan generation (minimal route graph)."""

from __future__ import annotations

from money_map.core.model import PlanStep, RoutePlan, Variant
from money_map.core.rules import evaluate_legal


def build_plan(profile: dict, variant: Variant, rulepack) -> RoutePlan:
    legal = evaluate_legal(rulepack, variant)
    prep_detail = "; ".join(variant.prep_steps) if variant.prep_steps else "No prep tasks provided."
    steps = [
        PlanStep("Confirm scope", f"Review summary: {variant.summary}"),
        PlanStep("Assess feasibility", "Validate time, capital, and assets requirements."),
        PlanStep("Prep tasks", prep_detail),
        PlanStep("Prepare assets", "Gather required assets and tooling."),
        PlanStep("Compliance check", "Complete compliance checklist before launch."),
        PlanStep("Setup operations", "Create basic workflow and tracking sheet."),
        PlanStep("Build offer", "Define the first offer and pricing range."),
        PlanStep("Pilot outreach", "Contact initial prospects for feedback."),
        PlanStep("Refine delivery", "Adjust offer based on pilot feedback."),
        PlanStep("Launch week", "Start serving first customers."),
        PlanStep("Review results", "Record early performance and decide next steps."),
    ]

    artifacts = [
        "artifacts/checklist.md",
        "artifacts/budget.yaml",
        "artifacts/outreach_message.txt",
    ]

    week_plan = {
        "week_1": ["Confirm scope", "Assess feasibility", "Prep tasks"],
        "week_2": ["Compliance check", "Setup operations", "Build offer"],
        "week_3": ["Pilot outreach", "Refine delivery"],
        "week_4": ["Launch week", "Review results"],
    }

    compliance_items = []
    for kit, items in rulepack.compliance_kits.items():
        compliance_items.append(f"{kit}: {', '.join(items)}")
    compliance_items.extend(legal.checklist)

    return RoutePlan(
        variant_id=variant.variant_id,
        steps=steps,
        artifacts=artifacts,
        week_plan=week_plan,
        compliance=compliance_items,
        legal_gate=legal.legal_gate,
        applied_rules=legal.applied_rules,
    )
