from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

from money_map.core.model import UserProfile
from money_map.i18n import t


def _load_default_profile(data_dir: Path) -> UserProfile:
    profile_path = data_dir.parent / "profiles" / "demo_fast_start.yaml"
    with profile_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return UserProfile.model_validate(data)


def render(data_dir: Path, lang: str) -> None:
    st.header(t("ui.profile.header", lang))
    if "profile" not in st.session_state:
        st.session_state["profile"] = _load_default_profile(data_dir)

    profile: UserProfile = st.session_state["profile"]

    with st.form("profile_form"):
        country_code = st.text_input(t("ui.profile.country", lang), profile.country_code)
        time_hours = st.number_input(
            t("ui.profile.time_hours", lang),
            min_value=1,
            max_value=80,
            value=profile.time_hours_per_week,
        )
        capital = st.number_input(
            t("ui.profile.capital", lang),
            min_value=0,
            max_value=1_000_000,
            value=profile.capital_eur,
        )
        language_level = st.text_input(t("ui.profile.language_level", lang), profile.language_level)
        skills = st.text_input(t("ui.profile.skills", lang), ", ".join(profile.skills))
        assets = st.text_input(t("ui.profile.assets", lang), ", ".join(profile.assets))
        constraints = st.text_input(
            t("ui.profile.constraints", lang), ", ".join(profile.constraints)
        )
        risk_tolerance = st.selectbox(
            t("ui.profile.risk_tolerance", lang),
            options=["low", "medium", "high"],
            index=["low", "medium", "high"].index(profile.risk_tolerance),
        )
        horizon_months = st.number_input(
            t("ui.profile.horizon_months", lang),
            min_value=1,
            max_value=36,
            value=profile.horizon_months,
        )
        target_net = st.number_input(
            t("ui.profile.target_net_monthly", lang),
            min_value=0,
            max_value=100_000,
            value=profile.target_net_monthly_eur or 0,
        )
        preferred_modes = st.text_input(
            t("ui.profile.preferred_modes", lang), ", ".join(profile.preferred_modes)
        )
        objective_preset = st.text_input(
            t("ui.profile.objective_preset", lang), profile.objective_preset
        )
        submitted = st.form_submit_button(t("ui.profile.save", lang))

    if submitted:
        st.session_state["profile"] = UserProfile(
            country_code=country_code,
            time_hours_per_week=int(time_hours),
            capital_eur=int(capital),
            language_level=language_level,
            skills=[item.strip() for item in skills.split(",") if item.strip()],
            assets=[item.strip() for item in assets.split(",") if item.strip()],
            constraints=[item.strip() for item in constraints.split(",") if item.strip()],
            risk_tolerance=risk_tolerance,
            horizon_months=int(horizon_months),
            target_net_monthly_eur=int(target_net) or None,
            preferred_modes=[item.strip() for item in preferred_modes.split(",") if item.strip()],
            objective_preset=objective_preset,
        )
        st.success(t("ui.profile.saved", lang))

    uploaded = st.file_uploader(t("ui.profile.upload", lang), type=["yaml", "yml"])
    if uploaded:
        data = yaml.safe_load(uploaded.getvalue()) or {}
        st.session_state["profile"] = UserProfile.model_validate(data)
        st.success(t("ui.profile.loaded", lang))
