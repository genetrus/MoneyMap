from money_map.app.api import validate_data


def test_validate_data_payload_has_expected_keys():
    report = validate_data()
    expected = {
        "dataset_version",
        "reviewed_at",
        "status",
        "stale",
        "staleness",
        "fatals",
        "warns",
    }
    assert expected.issubset(report.keys())
