from money_map.core.profile import validate_profile


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
