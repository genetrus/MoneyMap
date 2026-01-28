from __future__ import annotations

from pathlib import Path

import streamlit as st

from money_map.core.load import load_app_data
from money_map.core.model import UserProfile
from money_map.core.recommend import recommend
from money_map.i18n import t


REALITY_BLOCKERS = [
    "ui.reco.blocker_1",
    "ui.reco.blocker_2",
    "ui.reco.blocker_3",
]
REALITY_FIXES = [
    "ui.reco.fix_1",
    "ui.reco.fix_2",
    "ui.reco.fix_3",
]


def render(data_dir: Path, lang: str) -> None:
    st.header(t("ui.reco.header", lang))
    appdata = load_app_data(data_dir)

    profile: UserProfile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    objective = st.selectbox(
        t("ui.reco.objective_preset", lang),
        options=["fast_start", "balanced", "low_risk"],
        index=0,
    )

    if st.button(t("common.recommend", lang)):
        profile.objective_preset = objective
        result = recommend(profile, appdata, top_n=5)
        st.session_state["recommendations"] = result

    result = st.session_state.get("recommendations")
    if result:
        variant_by_id = {variant.variant_id: variant for variant in appdata.variants}
        for item in result.ranked_variants:
            variant = variant_by_id[item["variant_id"]]
            st.subheader(t(variant.title_key, lang))
            st.write(t(variant.summary_key, lang))
            if st.button(t("ui.reco.select", lang, variant_id=variant.variant_id)):
                st.session_state["selected_variant_id"] = variant.variant_id

        st.markdown(f"### {t('ui.reco.reality_check', lang)}")
        st.write(f"**{t('ui.reco.blockers', lang)}**")
        for blocker in REALITY_BLOCKERS:
            st.write(f"- {t(blocker, lang)}")
        st.write(f"**{t('ui.reco.fixes', lang)}**")
        for fix in REALITY_FIXES:
            st.write(f"- {t(fix, lang)}")
