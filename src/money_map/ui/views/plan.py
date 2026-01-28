from __future__ import annotations

from pathlib import Path

import streamlit as st

from money_map.core.load import load_app_data
from money_map.core.model import UserProfile
from money_map.core.plan import build_plan
from money_map.i18n import t
from money_map.render.md import render_plan_md


def render(data_dir: Path, lang: str) -> None:
    st.header(t("ui.plan.header", lang))
    selected = st.session_state.get("selected_variant_id")
    if not selected:
        st.info(t("ui.plan.no_selection", lang))
        return

    profile: UserProfile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    appdata = load_app_data(data_dir)
    plan = build_plan(selected, profile, appdata)
    st.markdown(render_plan_md(plan))
