"""Render result JSON."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from money_map.core.model import RecommendationVariant, RoutePlan


def render_result_json(
    profile: dict,
    recommendation: RecommendationVariant,
    plan: RoutePlan,
    *,
    diagnostics: dict[str, Any] | None = None,
    profile_hash: str | None = None,
    run_id: str | None = None,
    applied_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    variant = recommendation.variant
    applied_rules = plan.applied_rules
    diagnostics = diagnostics or {}
    return {
        "run_id": run_id,
        "profile_hash": profile_hash,
        "profile": profile,
        "variant_id": variant.variant_id,
        "variant_title": variant.title,
        "score": recommendation.score,
        "staleness": recommendation.staleness,
        "explanations": {
            "pros": recommendation.pros,
            "cons": recommendation.cons,
            "legal_checklist": plan.compliance,
        },
        "diagnostics": diagnostics,
        "applied_filters": applied_filters or {},
        "feasibility": asdict(recommendation.feasibility),
        "economics": asdict(recommendation.economics),
        "legal": {
            "legal_gate": plan.legal_gate,
            "checklist": plan.compliance,
            "applied_rule_ids": [rule.rule_id for rule in applied_rules],
            "applied_rules": [asdict(rule) for rule in applied_rules],
        },
        "plan": {
            "steps": [step.title for step in plan.steps],
            "artifacts": plan.artifacts,
            "week_plan": plan.week_plan,
            "staleness": plan.staleness,
        },
    }
