from money_map.core.model import StalenessPolicy
from money_map.core.staleness import evaluate_staleness


def test_evaluate_staleness_flags_old_date():
    policy = StalenessPolicy(stale_after_days=30)

    result = evaluate_staleness("2000-01-01", policy, label="rulepack")

    assert result.is_stale
    assert result.severity == "warn"
    assert result.age_days is not None
    assert result.age_days > policy.stale_after_days


def test_evaluate_staleness_invalid_date_marks_fatal():
    policy = StalenessPolicy(stale_after_days=30)

    result = evaluate_staleness("not-a-date", policy, label="rulepack")

    assert result.severity == "fatal"
    assert result.is_stale is False
