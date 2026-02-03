"""Staleness evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from money_map.core.model import StalenessPolicy

_DATE_FORMATS = ["%Y-%m-%d"]


@dataclass(frozen=True)
class StalenessResult:
    is_stale: bool
    age_days: int | None
    threshold_days: int
    severity: str
    message: str


def is_freshness_unknown(result: StalenessResult) -> bool:
    return result.severity == "fatal"


def _parse_date(value: str) -> date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def evaluate_staleness(
    reviewed_at: object,
    policy: StalenessPolicy,
    label: str = "data",
) -> StalenessResult:
    if reviewed_at is None:
        parsed = None
    elif isinstance(reviewed_at, datetime):
        parsed = reviewed_at.date()
    elif isinstance(reviewed_at, date):
        parsed = reviewed_at
    elif isinstance(reviewed_at, str):
        value = reviewed_at.strip()
        parsed = _parse_date(value) if value else None
    else:
        parsed = None
    threshold = int(policy.stale_after_days)
    if not parsed:
        return StalenessResult(
            is_stale=False,
            age_days=None,
            threshold_days=threshold,
            severity="fatal",
            message=f"{label} reviewed_at is missing or invalid.",
        )

    age_days = (date.today() - parsed).days
    is_stale = age_days > threshold
    severity = "warn" if is_stale else "ok"
    state = "stale" if is_stale else "fresh"
    return StalenessResult(
        is_stale=is_stale,
        age_days=age_days,
        threshold_days=threshold,
        severity=severity,
        message=f"{label} is {state} ({age_days} days old, threshold {threshold}).",
    )
