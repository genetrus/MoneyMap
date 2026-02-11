from money_map.ui.session_state import (
    DEFAULT_FILTERS,
    compute_filters_hash,
    initialize_defaults,
    reset_downstream_for_profile_change,
    sync_dataset_meta,
    sync_filters_and_objective,
)


def test_initialize_defaults_contains_schema_keys() -> None:
    state = {}
    initialize_defaults(state)

    assert state["data_dir"] == "data"
    assert state["view_mode"] == "User"
    assert state["selected_variant_id"] == ""
    assert state["filters"]["top_n"] == DEFAULT_FILTERS["top_n"]


def test_sync_filters_and_objective_resets_downstream_on_change() -> None:
    state = {
        "filters": DEFAULT_FILTERS.copy(),
        "filters_hash": compute_filters_hash(DEFAULT_FILTERS),
        "objective_preset": "fastest_money",
        "recommendations": object(),
        "recommend_diagnostics": {"a": 1},
        "last_recommendations": object(),
        "plan": {"ok": True},
    }

    changed = sync_filters_and_objective(
        state,
        filters={**DEFAULT_FILTERS, "max_time_to_money_days": 14},
        objective_preset="fastest_money",
    )

    assert changed is True
    assert state["recommendations"] is None
    assert state["recommend_diagnostics"] is None
    assert state["last_recommendations"] is None
    assert state["plan"] is None


def test_sync_dataset_meta_resets_all_except_view_mode() -> None:
    state = {
        "view_mode": "Developer",
        "dataset_signature": "data|v1|2026-01-01",
        "profile": {"name": "x"},
        "page": "recommendations",
        "selected_variant_id": "v-1",
        "plan": {"ready": True},
        "filters": {"foo": "bar"},
        "filters_hash": "x",
    }
    initialize_defaults(state)

    changed = sync_dataset_meta(
        state,
        data_dir="data",
        dataset_version="v2",
        reviewed_at="2026-02-01",
        staleness_level="warn",
        country="DE",
    )

    assert changed is True
    assert state["view_mode"] == "Developer"
    assert state["page"] == "data-status"
    assert state["selected_variant_id"] == ""
    assert state["plan"] is None
    assert state["dataset_version"] == "v2"


def test_reset_downstream_for_profile_change() -> None:
    state = {
        "selected_variant_id": "v-3",
        "plan": {"w": 1},
        "recommendations": [1],
        "recommend_diagnostics": {"x": 1},
        "last_recommendations": [2],
    }

    reset_downstream_for_profile_change(state)

    assert state["selected_variant_id"] == ""
    assert state["plan"] is None
    assert state["recommendations"] is None
    assert state["recommend_diagnostics"] is None
    assert state["last_recommendations"] is None
