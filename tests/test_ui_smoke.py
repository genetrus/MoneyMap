import importlib.util

import pytest


def test_ui_app_import_smoke():
    if importlib.util.find_spec("streamlit") is None:
        pytest.skip("streamlit is not installed")

    from money_map.ui import app as ui_app

    assert hasattr(ui_app, "run_app")
    assert callable(ui_app.run_app)
