from __future__ import annotations

import io
from pathlib import Path

import streamlit as st
import yaml

from money_map.core.load import load_app_data
from money_map.core.model import UserProfile
from money_map.core.plan import build_plan
from money_map.core.recommend import recommend
from money_map.i18n import t
from money_map.render.json import to_json
from money_map.render.md import render_plan_md


def render(data_dir: Path, lang: str) -> None:
    st.header(t("ui.export.header", lang))
    profile: UserProfile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    appdata = load_app_data(data_dir)

    if st.button(t("common.export", lang)):
        result = recommend(profile, appdata, top_n=5)
        variant_id = result.ranked_variants[0]["variant_id"]
        plan = build_plan(variant_id, profile, appdata)

        profile_bytes = yaml.safe_dump(profile.model_dump(), sort_keys=True).encode("utf-8")
        result_bytes = to_json(result.model_dump()).encode("utf-8")
        plan_bytes = render_plan_md(plan).encode("utf-8")

        st.download_button(
            t("ui.export.download_profile", lang),
            data=io.BytesIO(profile_bytes),
            file_name="profile.yaml",
        )
        st.download_button(
            t("ui.export.download_result", lang),
            data=io.BytesIO(result_bytes),
            file_name="result.json",
        )
        st.download_button(
            t("ui.export.download_plan", lang),
            data=io.BytesIO(plan_bytes),
            file_name="plan.md",
        )
