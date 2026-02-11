import importlib.util

import pytest


def test_selected_ids_from_state_prefers_unified_keys() -> None:
    if importlib.util.find_spec("streamlit") is None:
        pytest.skip("streamlit not installed in test environment")

    from money_map.ui.components import selected_ids_from_state

    state = {
        "selected_cell_id": "A2",
        "explore_selected_cell": "A1",
        "selected_taxonomy_id": "service_fee",
        "selected_variant_id": "v-123",
        "selected_bridge_id": "A1->A2",
        "selected_path_id": "path-1",
    }

    selected = selected_ids_from_state(state)
    assert selected["cell"] == "A2"
    assert selected["taxonomy"] == "service_fee"
    assert selected["variant"] == "v-123"
    assert selected["bridge"] == "A1->A2"
    assert selected["path"] == "path-1"
