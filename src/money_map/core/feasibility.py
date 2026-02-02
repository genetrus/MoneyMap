"""Feasibility checks for variants."""

from __future__ import annotations

from money_map.core.model import FeasibilityResult, Variant


_LANGUAGE_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2", "native"]


def _language_rank(level: str | None) -> int:
    if not level:
        return -1
    try:
        return _LANGUAGE_ORDER.index(level)
    except ValueError:
        return -1


def _meets_language_requirement(profile_level: str | None, min_level: str | None) -> bool:
    if not min_level:
        return True
    return _language_rank(profile_level) >= _language_rank(min_level)


def assess_feasibility(profile: dict, variant: Variant) -> FeasibilityResult:
    requirements = variant.feasibility
    blockers: list[str] = []

    min_language = requirements.get("min_language_level")
    if min_language and not _meets_language_requirement(profile.get("language_level"), min_language):
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
        status = "not_feasible" if len(blockers) >= 3 else "feasible_with_prep"

    return FeasibilityResult(status=status, blockers=blockers[:3], prep_steps=variant.prep_steps)
