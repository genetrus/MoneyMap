"""Feasibility checks for variants."""

from __future__ import annotations

from money_map.core.model import FeasibilityResult, Variant


def assess_feasibility(profile: dict, variant: Variant) -> FeasibilityResult:
    requirements = variant.feasibility
    blockers: list[str] = []

    min_language = requirements.get("min_language_level")
    if min_language and profile.get("language_level") not in [min_language, "B2", "C1", "C2", "native"]:
        blockers.append(f"Language level below {min_language}")

    min_capital = requirements.get("min_capital", 0)
    if profile.get("capital_eur", 0) < min_capital:
        blockers.append("Insufficient startup capital")

    min_time = requirements.get("min_time_per_week", 0)
    if profile.get("time_per_week", 0) < min_time:
        blockers.append("Not enough weekly time")

    required_assets = set(requirements.get("required_assets", []))
    available_assets = set(profile.get("assets", []))
    missing_assets = sorted(required_assets - available_assets)
    if missing_assets:
        blockers.append(f"Missing assets: {', '.join(missing_assets)}")

    status = "feasible"
    if blockers:
        status = "not_feasible" if len(blockers) >= 3 else "with_prep"

    return FeasibilityResult(status=status, blockers=blockers[:3], prep_steps=variant.prep_steps)
