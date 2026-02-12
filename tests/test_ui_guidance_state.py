from money_map.ui.guidance import (
    compute_guidance_runtime,
    initialize_guide_state,
    load_guide_steps,
)


def test_load_guide_steps_has_required_contract_fields() -> None:
    steps = load_guide_steps()

    assert len(steps) >= 5
    first = steps[0]
    assert first["id"] == "step_data_status"
    assert isinstance(first.get("prerequisites"), list)
    assert isinstance(first.get("completion"), list)
    assert isinstance(first.get("primary_action"), dict)


def test_initialize_guide_state_defaults_shape() -> None:
    state = {}
    guide_state = initialize_guide_state(state)

    assert guide_state["enabled"] is True
    assert guide_state["current_step_id"] == "step_data_status"
    assert guide_state["completed_steps"] == []
    assert guide_state["skipped_steps"] == []
    assert guide_state["dismissed_tooltips"] == []


def test_compute_guidance_runtime_returns_single_current_step_and_primary_action() -> None:
    state = {
        "profile": {
            "name": "Demo",
            "country": "DE",
            "location": "Berlin",
            "objective": "fastest_money",
            "language_level": "B1",
            "capital_eur": 300,
            "time_per_week": 10,
            "assets": ["laptop"],
            "skills": ["customer_service"],
            "constraints": [],
        },
        "selected_variant_id": "v-1",
        "plan": {"steps": ["a"]},
        "export_paths": None,
    }
    initialize_guide_state(state)

    runtime = compute_guidance_runtime(state, validate_report={"status": "valid"})

    assert runtime["is_guided"] is True
    assert runtime["current_step"]["id"] == "step_export"
    assert runtime["next_step"]["id"] == "step_export"
    assert runtime["primary_action"]["target_page"] == "export"
    assert runtime["primary_action"]["disabled"] is True


def test_compute_guidance_runtime_blockers_and_resolver_for_profile_step() -> None:
    state = {
        "profile": {"name": "Draft"},
        "selected_variant_id": "",
        "plan": None,
        "export_paths": None,
    }
    initialize_guide_state(state)

    runtime = compute_guidance_runtime(state, validate_report={"status": "valid"})

    assert runtime["current_step"]["id"] == "step_profile"
    assert runtime["primary_action"]["disabled"] is True
    assert runtime["blockers"]
    assert runtime["blockers_resolver"]["focus_page"] == "profile"
    assert "time_per_week" in runtime["blockers_resolver"]["highlight_fields"]


def test_compute_guidance_runtime_respects_disabled_mode() -> None:
    state = {"guide_state": {"enabled": False}}
    initialize_guide_state(state)

    runtime = compute_guidance_runtime(state, validate_report={"status": "invalid"})

    assert runtime["is_guided"] is False
    assert runtime["current_step"]["id"] == "step_data_status"
