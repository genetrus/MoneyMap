from __future__ import annotations

from money_map.core.model import RoutePlan, UserProfile
from money_map.core.load import AppData


def build_plan(
    selected_variant_id: str, profile: UserProfile, appdata: AppData
) -> RoutePlan:
    _ = profile
    _ = appdata
    return RoutePlan(
        selected_variant_id=selected_variant_id,
        steps=[
            {"step": "Define scope and assumptions", "status": "stub"},
            {"step": "Validate legal constraints", "status": "stub"},
            {"step": "Prepare launch checklist", "status": "stub"},
        ],
        week_plan=[
            {"week": 1, "focus": "Research"},
            {"week": 2, "focus": "Prototype"},
            {"week": 3, "focus": "Validation"},
            {"week": 4, "focus": "Launch prep"},
        ],
        aggregated_checklist=["Compliance check (stub)", "Budget check (stub)"],
        artifacts=["plan.md", "result.json"],
    )
