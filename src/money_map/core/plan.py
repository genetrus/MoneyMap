from __future__ import annotations

from datetime import date, timedelta

from money_map.core.load import AppData
from money_map.core.model import RoutePlan, UserProfile, Variant
from money_map.core.rules import evaluate_rulepack


def _chunk(items: list[str], chunks: int) -> list[list[str]]:
    if not items:
        return [[] for _ in range(chunks)]
    size = max(1, len(items) // chunks)
    split: list[list[str]] = []
    index = 0
    for _ in range(chunks - 1):
        split.append(items[index : index + size])
        index += size
    split.append(items[index:])
    while len(split) < chunks:
        split.append([])
    return split


def _tagged_actions(variant: Variant) -> list[str]:
    actions: list[str] = []
    tags = set(variant.tags)
    if "inventory" in tags:
        actions.append("planner.action.source_suppliers")
    if "content" in tags:
        actions.append("planner.action.outline_content")
    if "automation" in tags:
        actions.append("planner.action.map_processes")
    if "community" in tags:
        actions.append("planner.action.seed_community")
    return actions


def build_plan(selected_variant_id: str, profile: UserProfile, appdata: AppData) -> RoutePlan:
    variant = next(
        (item for item in appdata.variants if item.variant_id == selected_variant_id),
        None,
    )
    if variant is None:
        raise ValueError(f"Unknown variant_id: {selected_variant_id}")

    rule_eval = evaluate_rulepack(profile, variant, appdata.rulepack, today=date.today())
    compliance_checklist = rule_eval.compliance_checklist
    checklist_chunks = _chunk(compliance_checklist, 4)

    base_week_actions = [
        [
            "planner.action.define_offer",
            "planner.action.check_compliance",
            "planner.action.setup_tools",
        ],
        [
            "planner.action.pilot_offer",
            "planner.action.first_revenue_attempt",
            "planner.action.collect_feedback",
        ],
        [
            "planner.action.scale_process",
            "planner.action.optimize_pricing",
            "planner.action.expand_channels",
        ],
        [
            "planner.action.stabilize_ops",
            "planner.action.review_metrics",
            "planner.action.plan_next_steps",
        ],
    ]
    tag_actions = _tagged_actions(variant)
    if tag_actions:
        base_week_actions[0].extend(tag_actions[:2])
        if len(tag_actions) > 2:
            base_week_actions[1].extend(tag_actions[2:])

    steps: list[dict] = []
    week_plan: list[dict] = []
    outputs = [
        ["planner.output.offer_sheet", "planner.output.compliance_checklist"],
        ["planner.output.pilot_log", "planner.output.feedback_log"],
        ["planner.output.scaling_plan", "planner.output.channel_log"],
        ["planner.output.review_summary", "planner.output.next_review_dates"],
    ]

    for index, actions in enumerate(base_week_actions, start=1):
        steps.append(
            {
                "week": index,
                "title_key": f"planner.week{index}.title",
                "actions": actions,
                "estimated_hours": profile.time_hours_per_week,
                "outputs": outputs[index - 1],
                "checks": checklist_chunks[index - 1],
            }
        )
        week_plan.append(
            {
                "week": index,
                "title_key": f"planner.week{index}.title",
                "tasks": actions,
            }
        )

    today = date.today()
    next_reviews = [
        {"item_key": "planner.review.legal", "due_date": today + timedelta(days=30)},
        {"item_key": "planner.review.market", "due_date": today + timedelta(days=60)},
        {"item_key": "planner.review.financials", "due_date": today + timedelta(days=90)},
    ]

    artifacts = [
        {
            "filename": "plan.md",
            "description_key": "planner.artifact.plan_md",
            "mime": "text/markdown",
        },
        {
            "filename": "result.json",
            "description_key": "planner.artifact.result_json",
            "mime": "application/json",
        },
        {
            "filename": "profile.yaml",
            "description_key": "planner.artifact.profile_yaml",
            "mime": "text/yaml",
        },
        {
            "filename": "checklist.md",
            "description_key": "planner.artifact.checklist_md",
            "mime": "text/markdown",
        },
    ]

    return RoutePlan(
        selected_variant_id=selected_variant_id,
        overview={
            "goal_variant_key": variant.title_key,
            "time_hours_per_week": profile.time_hours_per_week,
            "constraints": profile.constraints,
            "risk_tolerance": profile.risk_tolerance,
        },
        steps=steps,
        week_plan=week_plan,
        compliance_checklist=compliance_checklist,
        artifacts=artifacts,
        risks=["planner.risk.cash_flow", "planner.risk.compliance"],
        next_reviews=next_reviews,
    )
