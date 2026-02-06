"""Profile helpers."""

from __future__ import annotations

import hashlib
import json

ALLOWED_OBJECTIVES = {"fastest_money", "max_net"}
ALLOWED_LANGUAGE_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2", "native"}


def profile_hash(profile: dict) -> str:
    payload = json.dumps(profile, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_profile(profile: dict) -> dict:
    missing: list[str] = []
    warnings: list[str] = []

    country = str(profile.get("country", "")).strip()
    if not country:
        missing.append("country")
    elif country != "DE":
        warnings.append("MVP currently supports country=DE only.")

    language_level = str(profile.get("language_level", "")).strip()
    if not language_level:
        missing.append("language_level")
    elif language_level not in ALLOWED_LANGUAGE_LEVELS:
        warnings.append("Language level should be one of A1/A2/B1/B2/C1/C2/native.")

    objective = str(profile.get("objective", "")).strip()
    if not objective:
        missing.append("objective")
    elif objective not in ALLOWED_OBJECTIVES:
        warnings.append("Objective preset should be fastest_money or max_net.")

    capital = profile.get("capital_eur")
    if capital is None:
        missing.append("capital_eur")
    elif not isinstance(capital, (int, float)):
        warnings.append("Capital must be a number in EUR.")
    elif capital < 0:
        warnings.append("Capital cannot be negative.")

    time_per_week = profile.get("time_per_week")
    if time_per_week is None:
        missing.append("time_per_week")
    elif not isinstance(time_per_week, (int, float)):
        warnings.append("Time per week must be a number.")
    elif time_per_week < 1:
        warnings.append("Time per week should be at least 1 hour for realistic recommendations.")
    elif time_per_week > 112:
        warnings.append("Time per week looks too high (>112h); check your input.")

    assets = profile.get("assets", [])
    skills = profile.get("skills", [])
    if not assets:
        warnings.append("Assets are empty; feasibility may be less precise.")
    if not skills:
        warnings.append("Skills are empty; recommendations may be generic.")

    is_ready = (not missing) and not any(
        message in warnings
        for message in (
            "Capital cannot be negative.",
            "Time per week should be at least 1 hour for realistic recommendations.",
            "MVP currently supports country=DE only.",
        )
    )
    return {
        "status": "ready" if is_ready else "draft",
        "is_ready": is_ready,
        "missing": missing,
        "warnings": warnings,
    }


def profile_reproducibility_state(profile: dict, previous_hash: str | None = None) -> dict:
    current_hash = profile_hash(profile)
    objective_preset = str(profile.get("objective", "fastest_money") or "fastest_money")
    changed = previous_hash is not None and previous_hash != current_hash
    return {
        "profile_hash": current_hash,
        "objective_preset": objective_preset,
        "changed": changed,
    }
