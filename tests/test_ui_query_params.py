from money_map.ui.navigation import resolve_page_from_query


def test_resolve_page_from_query_handles_valid_and_invalid() -> None:
    default = "Data status"

    assert resolve_page_from_query({}, default) == default
    assert resolve_page_from_query({"page": "plan"}, default) == "Plan"
    assert resolve_page_from_query({"page": ["export"]}, default) == "Export"
    assert resolve_page_from_query({"page": "unknown"}, default) == default
