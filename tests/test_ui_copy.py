from money_map.ui.copy import copy_text, load_copy


def test_load_copy_ru_has_mode_keys() -> None:
    payload = load_copy("ru")
    assert payload["app"]["mode_guided"] == "Вести меня"
    assert payload["app"]["mode_explorer"] == "Я сам"


def test_copy_text_returns_default_for_missing_key() -> None:
    assert copy_text("missing.path", "fallback") == "fallback"


def test_copy_text_supports_formatting() -> None:
    text = copy_text("guided.next_step_cta", "Continue → {page}", page="Plan")
    assert text == "Continue → Plan"
