import pytest


def test_ui_import():
    pytest.importorskip("streamlit")
    import money_map.ui

    assert money_map.ui.__name__ == "money_map.ui"
