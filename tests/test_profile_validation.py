from money_map.core.profile import profile_reproducibility_state, validate_profile


def test_profile_ready_with_minimum_fields() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "objective": "fastest_money",
        "capital_eur": 0,
        "time_per_week": 10,
        "assets": ["laptop"],
        "skills": ["customer_service"],
        "constraints": [],
    }

    result = validate_profile(profile)

    assert result["status"] == "ready"
    assert result["is_ready"] is True
    assert result["missing"] == []


def test_profile_draft_with_missing_required_fields() -> None:
    profile = {
        "country": "",
        "language_level": "",
        "objective": "",
        "capital_eur": None,
        "time_per_week": None,
        "assets": [],
        "skills": [],
        "constraints": [],
    }

    result = validate_profile(profile)

    assert result["status"] == "draft"
    assert set(result["missing"]) == {
        "country",
        "language_level",
        "objective",
        "capital_eur",
        "time_per_week",
    }


def test_profile_draft_with_out_of_range_values() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "objective": "fastest_money",
        "capital_eur": -10,
        "time_per_week": 0,
        "assets": [],
        "skills": [],
        "constraints": [],
    }

    result = validate_profile(profile)

    assert result["is_ready"] is False
    assert "Capital cannot be negative." in result["warnings"]
    assert (
        "Time per week should be at least 1 hour for realistic recommendations."
        in result["warnings"]
    )


def test_profile_reproducibility_state_hash_is_deterministic() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "objective": "max_net",
        "capital_eur": 100,
        "time_per_week": 8,
        "assets": ["laptop"],
        "skills": ["sales"],
        "constraints": [],
    }

    state1 = profile_reproducibility_state(profile)
    state2 = profile_reproducibility_state(profile, previous_hash=state1["profile_hash"])

    assert state1["profile_hash"] == state2["profile_hash"]
    assert state1["objective_preset"] == "max_net"
    assert state2["changed"] is False


def test_profile_reproducibility_state_detects_change() -> None:
    profile = {
        "country": "DE",
        "language_level": "B1",
        "objective": "fastest_money",
        "capital_eur": 100,
        "time_per_week": 8,
        "assets": ["laptop"],
        "skills": ["sales"],
        "constraints": [],
    }
    baseline = profile_reproducibility_state(profile)

    changed_profile = {**profile, "time_per_week": 12}
    changed = profile_reproducibility_state(changed_profile, previous_hash=baseline["profile_hash"])

    assert changed["changed"] is True
