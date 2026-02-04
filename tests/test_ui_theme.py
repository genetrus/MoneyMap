from money_map.ui.theme import THEME_PRESETS, build_theme_css


def test_theme_palettes_have_required_tokens() -> None:
    required = {
        "bg",
        "text",
        "muted",
        "card_bg",
        "card_border",
        "sidebar_bg",
        "nav_hover_bg",
        "nav_active_bg",
        "nav_active_border",
        "nav_active_bar",
        "nav_icon",
        "nav_icon_active",
    }
    for name, palette in THEME_PRESETS.items():
        missing = required.difference(palette.keys())
        assert not missing, f"Theme {name} missing keys: {sorted(missing)}"


def test_build_theme_css_contains_key_selectors() -> None:
    css = build_theme_css("Light")
    assert "--mm-bg" in css
    assert ".mm-nav-link" in css
    assert ".data-status" in css
