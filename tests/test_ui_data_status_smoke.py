from money_map.ui import app as ui_app


def test_data_status_view_imports_and_validates() -> None:
    report = ui_app._get_validation()
    assert "dataset_version" in report
