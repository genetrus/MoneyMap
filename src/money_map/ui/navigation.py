"""Navigation helpers for the Streamlit UI."""

from __future__ import annotations

NAV_ITEMS: list[tuple[str, str]] = [
    ("Data status", "data-status"),
    ("Profile", "profile"),
    ("Recommendations", "recommendations"),
    ("Plan", "plan"),
    ("Export", "export"),
]

NAV_LABEL_BY_SLUG = {slug: label for label, slug in NAV_ITEMS}
NAV_SLUG_BY_LABEL = {label: slug for label, slug in NAV_ITEMS}
NAV_PAGES = list(NAV_SLUG_BY_LABEL)


def resolve_page_from_query(params: dict | None, default: str) -> str:
    if not params:
        return default
    page = params.get("page")
    if isinstance(page, (list, tuple)):
        page = page[0] if page else None
    if isinstance(page, str):
        resolved = NAV_LABEL_BY_SLUG.get(page)
        if resolved:
            return page
    return default
