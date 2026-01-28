from pathlib import Path

from money_map.core.validate import validate_app_data


def test_validate_seed_data() -> None:
    fatals, _ = validate_app_data(Path("data"))
    assert fatals == []
