import importlib

import pytest


def test_ui_import_smoke():
    pytest.importorskip("streamlit")
    module = importlib.import_module("money_map.ui.app")
    assert module.__name__ == "money_map.ui.app"
