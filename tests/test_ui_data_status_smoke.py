import importlib.util

import pytest


def test_data_status_view_imports_and_validates() -> None:
    if importlib.util.find_spec("streamlit") is None:
        pytest.skip("streamlit not installed in test environment")
    from money_map.ui import app as ui_app

    report = ui_app._get_validation()
    assert "dataset_version" in report
