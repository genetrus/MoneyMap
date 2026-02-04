import importlib.util
import os

import pytest


def test_ui_app_import_smoke():
    if importlib.util.find_spec("streamlit") is None:
        message = (
            'Streamlit is not installed. Install UI deps with: python -m pip install -e ".[ui]"'
        )
        if (os.getenv("MM_UI_CHECK") or "optional").lower() == "required":
            pytest.fail(message)
        pytest.skip(message)

    from money_map.ui import app as ui_app

    assert hasattr(ui_app, "run_app")
    assert callable(ui_app.run_app)
