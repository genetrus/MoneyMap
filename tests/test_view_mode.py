from money_map.ui.data_status import data_status_visibility
from money_map.ui.view_mode import DEFAULT_VIEW_MODE


def test_data_status_visibility_defaults_to_user_mode() -> None:
    visibility = data_status_visibility(DEFAULT_VIEW_MODE)

    assert visibility["show_validate_report"] is False
    assert visibility["show_raw_report_json"] is False


def test_data_status_visibility_developer_mode_shows_details() -> None:
    visibility = data_status_visibility("Developer")

    assert visibility["show_validate_report"] is True
    assert visibility["show_raw_report_json"] is True
