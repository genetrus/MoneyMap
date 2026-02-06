from __future__ import annotations

from datetime import date, timedelta

from money_map.core.model import StalenessPolicy
from money_map.core.staleness import evaluate_staleness


def test_staleness_warn_without_hard_stale() -> None:
    policy = StalenessPolicy(warn_after_days=10, hard_after_days=30)
    reviewed_at = (date.today() - timedelta(days=20)).isoformat()

    result = evaluate_staleness(reviewed_at, policy, label="rulepack")

    assert result.is_stale is True
    assert result.is_hard_stale is False
    assert result.severity == "warn"


def test_staleness_hard_stale_sets_fatal_severity() -> None:
    policy = StalenessPolicy(warn_after_days=10, hard_after_days=30)
    reviewed_at = (date.today() - timedelta(days=45)).isoformat()

    result = evaluate_staleness(reviewed_at, policy, label="rulepack")

    assert result.is_stale is True
    assert result.is_hard_stale is True
    assert result.severity == "fatal"


def test_hard_after_days_auto_clamped_to_warn_after_days() -> None:
    policy = StalenessPolicy(warn_after_days=20, hard_after_days=5)

    assert policy.hard_after_days == 20
