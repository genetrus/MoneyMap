"""Helpers for the Data status page."""

from __future__ import annotations


def data_status_visibility(view_mode: str) -> dict[str, bool]:
    return {
        "show_validate_report": True,
        "show_validation_summary": True,
        "show_raw_report_json": True,
        "show_staleness_details": True,
        "show_data_sources": True,
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
