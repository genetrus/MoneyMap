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


def user_alert_for_status(status: str) -> tuple[str, str] | None:
    if status == "invalid":
        return (
            "error",
            "**Data is invalid**\n\n"
            "Some required data checks failed. Results may be unreliable.\n\n"
            "Switch to Developer mode for details.",
        )
    if status == "stale":
        return (
            "warning",
            "**Data is stale**\n\n"
            "The dataset review date is older than the staleness policy. Results may be "
            "cautious.\n\n"
            "Switch to Developer mode for details.",
        )
    return None
