"""Helpers for the Data status page."""

from __future__ import annotations


def data_status_visibility(view_mode: str) -> dict[str, bool]:
    is_developer = view_mode == "Developer"
    return {
        "show_validate_report": is_developer,
        "show_validation_summary": is_developer,
        "show_raw_report_json": is_developer,
        "show_staleness_details": is_developer,
        "show_data_sources": is_developer,
    }
