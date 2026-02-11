from money_map.ui.status_tokens import (
    confidence_dots,
    get_feasibility_token,
    get_legal_token,
    get_staleness_token,
)


def test_feasibility_tokens_are_standardized() -> None:
    assert get_feasibility_token("feasible")[0].startswith("✅")
    assert get_feasibility_token("feasible_with_prep")[0].startswith("🟧")
    assert get_feasibility_token("not_feasible")[0].startswith("⛔")


def test_legal_tokens_are_standardized() -> None:
    assert get_legal_token("ok")[0].startswith("✅")
    assert get_legal_token("require_check")[0].startswith("❓")
    assert get_legal_token("blocked")[0].startswith("⛔")


def test_staleness_tokens_are_standardized() -> None:
    assert get_staleness_token("ok")[0].endswith("OK")
    assert get_staleness_token("stale")[0].endswith("WARN")
    assert get_staleness_token("invalid")[0].endswith("HARD")


def test_confidence_dots_handles_numeric_and_text() -> None:
    assert confidence_dots("low") == "●●○○○"
    assert confidence_dots(0.8) == "●●●●○"
    assert confidence_dots(5) == "●●●●●"
