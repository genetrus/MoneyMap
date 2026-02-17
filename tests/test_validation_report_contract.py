from __future__ import annotations

from dataclasses import replace

from money_map.app.api import validate_data
from money_map.core.load import load_app_data
from money_map.core.validate import validate


def _issue_codes(issues: list[dict]) -> list[str]:
    return [issue.get("code", "") for issue in issues if issue.get("code")]


def test_validation_report_status_rules() -> None:
    app_data = load_app_data()
    report = validate(app_data)
    assert report.status == "valid"

    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    stale_report = validate(replace(app_data, rulepack=stale_rulepack))
    assert stale_report.status == "stale"

    invalid_meta = replace(app_data.meta, dataset_version="")
    invalid_report = validate(replace(app_data, meta=invalid_meta))
    assert invalid_report.status == "invalid"


def test_validate_report_contract_keys() -> None:
    report = validate_data("data")
    required = {
        "status",
        "dataset_version",
        "reviewed_at",
        "dataset_reviewed_at",
        "stale",
        "staleness_policy_days",
        "generated_at",
        "fatals",
        "warns",
    }
    assert required.issubset(report.keys())

    for issue in report["fatals"] + report["warns"]:
        assert "code" in issue


def test_stale_warnings_emit_codes() -> None:
    app_data = load_app_data()
    stale_rulepack = replace(app_data.rulepack, reviewed_at="2000-01-01")
    report = validate(replace(app_data, rulepack=stale_rulepack))
    warn_codes = _issue_codes(report.warns)
    assert "STALE_RULEPACK" in warn_codes or "STALE_RULEPACK_HARD" in warn_codes
