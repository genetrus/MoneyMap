"""Staleness evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from money_map.core.model import StalenessPolicy

_DATE_FORMATS = ["%Y-%m-%d"]


@dataclass(frozen=True)
class StalenessResult:
    is_stale: bool
    is_hard_stale: bool
    age_days: int | None
    warn_after_days: int
    hard_after_days: int
    severity: str
    message: str


def is_freshness_unknown(result: StalenessResult) -> bool:
    return result.age_days is None


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
    invalid_severity: str = "fatal",
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

    warn_after_days = int(policy.warn_after_days)
    hard_after_days = int(policy.hard_after_days)
    if hard_after_days < warn_after_days:
        hard_after_days = warn_after_days

    if not parsed:
        return StalenessResult(
            is_stale=False,
            is_hard_stale=False,
            age_days=None,
            warn_after_days=warn_after_days,
            hard_after_days=hard_after_days,
            severity=invalid_severity,
            message=f"{label} reviewed_at is missing or invalid.",
        )

    age_days = (date.today() - parsed).days
    is_hard_stale = age_days > hard_after_days
    is_stale = age_days > warn_after_days

    if is_hard_stale:
        severity = "fatal"
        state = "hard-stale"
    elif is_stale:
        severity = "warn"
        state = "stale"
    else:
        severity = "ok"
        state = "fresh"

    return StalenessResult(
        is_stale=is_stale,
        is_hard_stale=is_hard_stale,
        age_days=age_days,
        warn_after_days=warn_after_days,
        hard_after_days=hard_after_days,
        severity=severity,
        message=(
            f"{label} is {state} ({age_days} days old, warn after {warn_after_days}, "
            f"hard after {hard_after_days})."
        ),
    )
