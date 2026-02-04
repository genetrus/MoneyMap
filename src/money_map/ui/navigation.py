"""Navigation helpers for the Streamlit UI."""

from __future__ import annotations

NAV_ITEMS: list[tuple[str, str]] = [
    ("Data status", "data-status"),
    ("Profile", "profile"),
    ("Recommendations", "recommendations"),
    ("Plan", "plan"),
    ("Export", "export"),
]

NAV_PAGES = [label for label, _ in NAV_ITEMS]


def resolve_page_from_query(params: dict | None, default: str) -> str:
    if not params:
        return default
    page = params.get("page")
    if isinstance(page, (list, tuple)):
        page = page[0] if page else None
    if isinstance(page, str) and page in NAV_PAGES:
        return page
    return default
