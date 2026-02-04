from __future__ import annotations

from money_map.app.api import validate_data


def test_validate_data_contains_expected_fields() -> None:
    report = validate_data("data")
    assert report["status"] in {"valid", "invalid"}
    assert "dataset_version" in report
    assert "reviewed_at" in report
    assert "warns" in report
    assert "fatals" in report
