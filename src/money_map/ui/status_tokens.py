"""Status tokens and normalization helpers for MoneyMap UI."""

from __future__ import annotations

from typing import Any

FEASIBILITY_TOKEN = {
    "feasible": ("✅ feasible", "badge-valid"),
    "feasible_with_prep": ("🟧 with_prep", "badge-stale"),
    "not_feasible": ("⛔ not_feasible", "badge-invalid"),
}

LEGAL_TOKEN = {
    "ok": ("✅ ok", "badge-valid"),
    "require_check": ("❓ require_check", "badge-stale"),
    "registration": ("🧾 registration", "badge-stale"),
    "license": ("🪪 license", "badge-stale"),
    "blocked": ("⛔ blocked", "badge-invalid"),
}

STALENESS_TOKEN = {
    "ok": ("✅ OK", "badge-valid"),
    "valid": ("✅ OK", "badge-valid"),
    "warn": ("🟧 WARN", "badge-stale"),
    "stale": ("🟧 WARN", "badge-stale"),
    "hard": ("⛔ HARD", "badge-invalid"),
    "invalid": ("⛔ HARD", "badge-invalid"),
}


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def get_feasibility_token(status: str | None) -> tuple[str, str]:
    return FEASIBILITY_TOKEN.get(_normalize(status), (f"❔ {status or 'unknown'}", "badge-stale"))


def get_legal_token(gate: str | None) -> tuple[str, str]:
    return LEGAL_TOKEN.get(_normalize(gate), (f"❔ {gate or 'unknown'}", "badge-stale"))


def get_staleness_token(level: str | None) -> tuple[str, str]:
    return STALENESS_TOKEN.get(_normalize(level), (f"❔ {level or 'unknown'}", "badge-stale"))


def confidence_dots(confidence: Any) -> str:
    if isinstance(confidence, str):
        mapping = {"low": 2, "medium": 3, "high": 4}
        score = mapping.get(confidence.strip().lower(), 0)
    elif isinstance(confidence, (int, float)):
        if 0 <= confidence <= 1:
            score = int(round(confidence * 5))
        else:
            score = int(round(confidence))
    else:
        score = 0

    score = max(0, min(5, score))
    return "●" * score + "○" * (5 - score)
