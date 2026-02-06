import importlib.util

import pytest

REQUIRED_PROFILE_KEYS = {
    "country",
    "time_per_week",
    "capital_eur",
    "language_level",
    "assets",
    "skills",
    "constraints",
    "objective",
}


def test_default_profile_contains_stage6_mvp_fields() -> None:
    if importlib.util.find_spec("streamlit") is None:
        pytest.skip("streamlit not installed in test environment")

    from money_map.ui.app import DEFAULT_PROFILE

    assert REQUIRED_PROFILE_KEYS.issubset(DEFAULT_PROFILE)
    assert DEFAULT_PROFILE["country"] == "DE"
