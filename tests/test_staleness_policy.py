from money_map.core.model import StalenessPolicy
from money_map.core.staleness import evaluate_staleness


def test_evaluate_staleness_warn_and_hard_flags():
    policy = StalenessPolicy(warn_after_days=30, hard_after_days=60)

    warn_result = evaluate_staleness("2000-01-01", policy, label="rulepack")

    assert warn_result.is_stale
    assert warn_result.is_hard_stale
    assert warn_result.severity == "fatal"
    assert warn_result.age_days is not None
    assert warn_result.age_days > policy.hard_after_days


def test_evaluate_staleness_invalid_date_marks_fatal():
    policy = StalenessPolicy(warn_after_days=30, hard_after_days=60)

    result = evaluate_staleness("not-a-date", policy, label="rulepack")

    assert result.severity == "fatal"
    assert result.is_stale is False
    assert result.is_hard_stale is False


def test_evaluate_staleness_handles_none_value():
    policy = StalenessPolicy(warn_after_days=30, hard_after_days=60)

    result = evaluate_staleness(None, policy, label="rulepack")

    assert result.severity == "fatal"
    assert result.is_stale is False
    assert result.is_hard_stale is False


def test_stale_after_days_alias_kept_for_back_compat():
    policy = StalenessPolicy(stale_after_days=45, hard_after_days=90)
    assert policy.warn_after_days == 45
    assert policy.hard_after_days == 90
