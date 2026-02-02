from money_map.core.load import load_app_data
from money_map.core.validate import validate


def test_validate_ok_on_seed_data():
    app_data = load_app_data()
    report = validate(app_data)
    assert report.status == "valid"
    assert report.fatals == []
