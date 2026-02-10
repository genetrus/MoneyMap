from money_map.ui.navigation import NAV_ITEMS


def test_navigation_contains_classify_page() -> None:
    slugs = [slug for _, slug in NAV_ITEMS]
    assert "classify" in slugs
