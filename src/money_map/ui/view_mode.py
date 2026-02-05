"""View mode helpers for Streamlit UI."""

from __future__ import annotations

DEFAULT_VIEW_MODE = "User"
VIEW_MODE_OPTIONS = ["User", "Developer"]


def get_view_mode() -> str:
    import streamlit as st

    st.session_state.setdefault("view_mode", DEFAULT_VIEW_MODE)
    value = st.session_state.get("view_mode", DEFAULT_VIEW_MODE)
    return value if value in VIEW_MODE_OPTIONS else DEFAULT_VIEW_MODE


def render_view_mode_control(location: str = "sidebar") -> None:
    import streamlit as st

    get_view_mode()
    control = st.sidebar if location == "sidebar" else st
    control.selectbox(
        "View mode",
        VIEW_MODE_OPTIONS,
        index=VIEW_MODE_OPTIONS.index(get_view_mode()),
        key="view_mode",
    )
