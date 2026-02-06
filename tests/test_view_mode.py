from money_map.ui.data_status import data_status_visibility, user_alert_for_status
from money_map.ui.view_mode import DEFAULT_VIEW_MODE


def test_data_status_visibility_defaults_to_user_mode() -> None:
    visibility = data_status_visibility(DEFAULT_VIEW_MODE)

    assert visibility["show_validate_report"] is True
    assert visibility["show_raw_report_json"] is True


def test_data_status_visibility_developer_mode_shows_details() -> None:
    visibility = data_status_visibility("Developer")

    assert visibility["show_validate_report"] is True
    assert visibility["show_raw_report_json"] is True


def test_user_alert_for_status_invalid() -> None:
    alert = user_alert_for_status("invalid")

    assert alert is not None
    kind, message = alert
    assert kind == "error"
    assert "Data is invalid" in message


def test_user_alert_for_status_stale() -> None:
    alert = user_alert_for_status("stale")

    assert alert is not None
    kind, message = alert
    assert kind == "warning"
    assert "Data is stale" in message


def test_user_alert_for_status_valid() -> None:
    assert user_alert_for_status("valid") is None
