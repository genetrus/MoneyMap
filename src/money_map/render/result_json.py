"""Render result JSON."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from money_map.core.model import RecommendationVariant, RoutePlan


def render_result_json(
    profile: dict,
    recommendation: RecommendationVariant,
    plan: RoutePlan,
) -> dict[str, Any]:
    variant = recommendation.variant
    return {
        "profile": profile,
        "variant_id": variant.variant_id,
        "variant_title": variant.title,
        "score": recommendation.score,
        "staleness": recommendation.staleness,
        "feasibility": asdict(recommendation.feasibility),
        "economics": asdict(recommendation.economics),
        "legal": {
            "legal_gate": plan.legal_gate,
            "checklist": plan.compliance,
            "applied_rules": [asdict(rule) for rule in plan.applied_rules],
        },
        "plan": {
            "steps": [step.title for step in plan.steps],
            "artifacts": plan.artifacts,
            "week_plan": plan.week_plan,
            "staleness": plan.staleness,
        },
    }
