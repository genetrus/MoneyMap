import importlib.util

import pytest


def test_capital_band_mapping() -> None:
    if importlib.util.find_spec("streamlit") is None:
        pytest.skip("streamlit not installed in test environment")

    from money_map.ui.app import _capital_band

    assert _capital_band(100) == "low"
    assert _capital_band(500) == "medium"
    assert _capital_band(5000) == "high"
