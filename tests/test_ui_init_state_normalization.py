import importlib.util

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("streamlit") is None,
    reason="streamlit not installed in test environment",
)
def test_normalize_profile_falls_back_to_default_for_none() -> None:
    from money_map.ui.app import DEFAULT_PROFILE, _normalize_profile

    profile = _normalize_profile(None)

    assert profile == DEFAULT_PROFILE
    assert profile is not DEFAULT_PROFILE


@pytest.mark.skipif(
    importlib.util.find_spec("streamlit") is None,
    reason="streamlit not installed in test environment",
)
def test_normalize_filters_merges_with_defaults() -> None:
    from money_map.ui.app import DEFAULT_FILTERS, _normalize_filters

    filters = _normalize_filters({"top_n": 3})

    assert filters["top_n"] == 3
    assert filters["max_time_to_money_days"] == DEFAULT_FILTERS["max_time_to_money_days"]
