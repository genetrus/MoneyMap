"""Plan generation (minimal route graph)."""

from __future__ import annotations

from dataclasses import asdict

from money_map.core.model import PlanStep, RoutePlan, StalenessPolicy, Variant
from money_map.core.rules import evaluate_legal
from money_map.core.staleness import evaluate_staleness


def build_plan(
    profile: dict,
    variant: Variant,
    rulepack,
    staleness_policy: StalenessPolicy,
) -> RoutePlan:
    legal = evaluate_legal(rulepack, variant, staleness_policy)
    prep_detail = "; ".join(variant.prep_steps) if variant.prep_steps else "No prep tasks provided."
    economics = variant.economics or {}
    time_to_money = economics.get("time_to_first_money_days_range", [])
    net_range = economics.get("typical_net_month_eur_range", [])
    cost_range = economics.get("costs_eur_range", [])
    economics_detail = (
        "Capture baseline economics: "
        f"time-to-first-money {time_to_money or 'n/a'} days, "
        f"net {net_range or 'n/a'} EUR/month, "
        f"costs {cost_range or 'n/a'} EUR."
    )
    steps = [
        PlanStep("Route: confirm scope", f"Review summary: {variant.summary}"),
        PlanStep("Prep: assess feasibility", "Validate time, capital, and assets requirements."),
        PlanStep("Prep tasks", f"Prep: complete tasks. {prep_detail}"),
        PlanStep("Prep: prepare assets", "Gather required assets and tooling."),
        PlanStep("Core: define offer", "Define the first offer, pricing, and delivery promise."),
        PlanStep("Core: setup operations", "Create workflow, calendar, and tracking sheet."),
        PlanStep("Compliance: legal checklist", "Complete compliance checklist before launch."),
        PlanStep("Economics: baseline tracking", economics_detail),
        PlanStep("Core: pilot outreach", "Contact initial prospects and gather feedback."),
        PlanStep("Core: refine delivery", "Adjust offer based on pilot feedback."),
        PlanStep("Checkpoint: first customer", "Confirm first paid engagement is completed."),
        PlanStep("Checkpoint: week 4 review", "Review results and decide scale or iterate."),
    ]

    artifacts = [
        "artifacts/checklist.md",
        "artifacts/budget.yaml",
        "artifacts/outreach_message.txt",
    ]

    week_plan = {
        "Week1": [
            "Route: confirm scope",
            "Prep: assess feasibility",
            "Prep tasks",
            "Prep: prepare assets",
        ],
        "Week2": [
            "Core: define offer",
            "Core: setup operations",
            "Compliance: legal checklist",
        ],
        "Week3": [
            "Economics: baseline tracking",
            "Core: pilot outreach",
            "Core: refine delivery",
        ],
        "Week4": [
            "Checkpoint: first customer",
            "Checkpoint: week 4 review",
        ],
    }

    compliance_items = []
    for kit in legal.compliance_kits:
        items = rulepack.compliance_kits.get(kit, [])
        if items:
            compliance_items.append(f"{kit}: {', '.join(items)}")
        else:
            compliance_items.append(f"{kit}: (kit definition missing)")
    compliance_items.extend(legal.checklist)

    rulepack_staleness = evaluate_staleness(
        rulepack.reviewed_at,
        staleness_policy,
        label="rulepack",
    )
    variant_staleness = evaluate_staleness(
        variant.review_date,
        staleness_policy,
        label=f"variant:{variant.variant_id}",
    )

    return RoutePlan(
        variant_id=variant.variant_id,
        steps=steps,
        artifacts=artifacts,
        week_plan=week_plan,
        compliance=compliance_items,
        legal_gate=legal.legal_gate,
        applied_rules=legal.applied_rules,
        staleness={
            "rulepack": asdict(rulepack_staleness),
            "variant": asdict(variant_staleness),
        },
    )
